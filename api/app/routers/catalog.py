"""Separate catalog assistant. Reuses the host and shop already connected."""
from __future__ import annotations

import asyncio
import json
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel
from fastapi.responses import Response

from app.services import catalog_metering, connection_store
from app.services.catalog_offer import catalog_offer
from app.services.catalog_product import PRODUCT_URL, catalog_product_url
from app.services.catalog_report import render_catalog_pdf
from app.services.catalog_apply import native_values
from app.services.catalog_pack import build_pack, with_model
from app.services.catalog_reader import normalize_odoo
from app.services.catalog_session import (
    begin_run,
    get_session,
    mark_injected,
    note_finished,
    note_window,
    public_session,
    publish_fixture,
    remember_pack,
    report_ready,
    run_public,
    start_listed,
    start_session,
    tick_session,
)
from app.services.catalog_shop import SelectedCatalogShop, shop_from_secrets
from app.services.entitlement_service import consume
from app.services.site_guard import extract_license
from app.services.sitemap_persist import IndexRecord, SitemapShop

router = APIRouter()

# Short-lived context cache so rapid /job polls (every 2s from FE) do not each
# re-run consume + multi XML-RPC and starve /offer on the thread pool.
_CONTEXT_CACHE: Dict[str, Dict[str, Any]] = {}
_CONTEXT_CACHE_LOCK = threading.Lock()
_CONTEXT_TTL_SEC = 8.0


def _context_cached(
    license: Optional[str],
    key: Optional[str],
    header: Optional[str],
) -> Dict[str, Any]:
    lic = extract_license(header, license, key) or ""
    now = time.monotonic()
    if lic:
        with _CONTEXT_CACHE_LOCK:
            hit = _CONTEXT_CACHE.get(lic)
            if hit and (now - hit.get("at", 0)) < _CONTEXT_TTL_SEC:
                return hit["ctx"]
    ctx = _context(license, key, header)
    if lic:
        with _CONTEXT_CACHE_LOCK:
            _CONTEXT_CACHE[lic] = {"at": time.monotonic(), "ctx": ctx}
    return ctx


def _invalidate_context(lic: Optional[str]) -> None:
    token = (lic or "").strip()
    if not token:
        return
    with _CONTEXT_CACHE_LOCK:
        _CONTEXT_CACHE.pop(token, None)


_CONFIRMED = ("sale", "done")
_LINE_FIELDS_FULL = [
    "name",
    "product_id",
    "product_uom_qty",
    "product_template_id",
    "aeo_site_url",
]
_LINE_FIELDS_MIN = ["name", "product_id", "product_uom_qty", "product_template_id"]


def _read_lines_for_order_ids(order_ids: List[int]) -> tuple[List[Dict[str, Any]], Optional[str]]:
    if not order_ids:
        return [], None
    from app.services.entitlement_service import _odoo_execute

    try:
        rows = _odoo_execute(
            "sale.order.line",
            "search_read",
            [("order_id", "in", order_ids)],
            fields=_LINE_FIELDS_FULL,
        )
    except Exception:
        rows = _odoo_execute(
            "sale.order.line",
            "search_read",
            [("order_id", "in", order_ids)],
            fields=_LINE_FIELDS_MIN,
        )
    if rows is None:
        return [], "odoo_unavailable"
    return [dict(row) for row in (rows or []) if isinstance(row, dict)], None


def _order_line_rows(sale_order_name: Optional[str]) -> tuple[List[Dict[str, Any]], Optional[str]]:
    """Return (rows, error). error set when Odoo could not be read (not when order has no lines)."""
    name = (sale_order_name or "").strip()
    if not name:
        return [], None
    try:
        from app.services.entitlement_service import _odoo_execute

        found = _odoo_execute(
            "sale.order",
            "search_read",
            [("name", "=", name)],
            fields=["id", "state", "partner_id"],
            limit=1,
        )
        if found is None:
            return [], "odoo_unavailable"
        found = found or []
        if not found:
            return [], None
        state = str(found[0].get("state") or "")
        if state and state not in _CONFIRMED:
            return [], None
        return _read_lines_for_order_ids([found[0]["id"]])
    except Exception as exc:
        return [], str(exc)[:200] or "odoo_unavailable"


def _partner_catalog_rows(
    partner_id: Optional[int],
    *,
    fallback_rows: Optional[List[Dict[str, Any]]] = None,
) -> tuple[List[Dict[str, Any]], Optional[str]]:
    """Confirmed catalog lines across all partner sale orders (not only license SO).

    Falls back to ``fallback_rows`` (license SO lines) when partner_id is missing
    or Odoo cannot list partner orders.
    """
    fallback = list(fallback_rows or [])
    try:
        pid = int(partner_id) if partner_id else 0
    except (TypeError, ValueError):
        pid = 0
    if not pid:
        return fallback, None
    try:
        from app.services.entitlement_service import _odoo_execute

        orders = _odoo_execute(
            "sale.order",
            "search_read",
            [("partner_id", "=", pid), ("state", "in", list(_CONFIRMED))],
            fields=["id", "name", "state"],
            limit=80,
        )
        if orders is None:
            return fallback, "odoo_unavailable"
        order_ids = [int(row["id"]) for row in (orders or []) if row.get("id")]
        rows, err = _read_lines_for_order_ids(order_ids)
        if err:
            return fallback, err
        # Prefer partner-wide rows; if empty keep license SO rows for diagnostics.
        return rows or fallback, None
    except Exception as exc:
        return fallback, str(exc)[:200] or "odoo_unavailable"


def _line_names(rows: List[Dict[str, Any]]) -> List[str]:
    lines: List[str] = []
    for row in rows:
        product = row.get("product_id")
        product_name = product[1] if isinstance(product, (list, tuple)) and len(product) > 1 else ""
        lines.append(" ".join(part for part in (row.get("name"), product_name) if part))
    return lines


def _metering_for(
    lic: Optional[str],
    host: Optional[str],
    rows: List[Dict[str, Any]],
    *,
    source_error: Optional[str] = None,
    needed_qty: Optional[int] = None,
) -> Dict[str, Any]:
    allowance = catalog_metering.allowance_from_rows(rows, host)
    snap = catalog_metering.metering_snapshot(
        lic or "",
        host,
        allowance,
        needed_qty=needed_qty,
    )
    out = {
        **snap,
        "acquire_url": catalog_product_url(
            False,
            host=host,
            quantity=needed_qty if needed_qty is not None else (snap.get("remaining") or 1),
        )
        or PRODUCT_URL,
    }
    if source_error:
        out["metering_error"] = source_error
    return out


def _context(
    license: Optional[str],
    key: Optional[str],
    header: Optional[str],
) -> Dict[str, Any]:
    lic = extract_license(header, license, key)
    consumed: Dict[str, Any] = {}
    if lic:
        consumed = consume(lic)
    host = consumed.get("aeo_site_url")
    order = consumed.get("sale_order_name")
    platforms: List[str] = []
    if lic:
        pack = connection_store.public_platforms(lic)
        for name, row in (pack.get("platforms") or {}).items():
            if isinstance(row, dict) and row.get("connected"):
                platforms.append(name)
        if not host:
            host = (pack.get("connection") or {}).get("url")
    rows, lines_error = _order_line_rows(order)
    partner_id = consumed.get("partner_id")
    meter_rows, partner_err = _partner_catalog_rows(partner_id, fallback_rows=rows)
    lines_error = lines_error or partner_err
    offer = catalog_offer(_line_names(rows), host, platforms)
    # Any valid active license for the site unlocks catalog (no second purchase).
    if consumed.get("allowed") is True and not offer.get("owned"):
        offer = {**offer, "owned": True}
    metering = _metering_for(lic, host, meter_rows, source_error=lines_error)
    offer = {**offer, **metering}
    return {
        "license": lic,
        "consumed": consumed,
        "offer": offer,
        "order": order,
        "host": host,
        "platforms": platforms,
        "allowance": metering["allowance"],
        "metering_error": lines_error,
    }


def _shop(lic: str, platform: Optional[str] = None) -> Any:
    secrets = connection_store.secrets_for(lic, platform)
    if not secrets.get("url"):
        raise HTTPException(status_code=409, detail="No hay una tienda conectada para este pedido.")
    try:
        return shop_from_secrets(secrets)
    except Exception as exc:
        raise HTTPException(status_code=409, detail=str(exc)[:240]) from exc


def _sitemap_from_session(state: Dict[str, Any], host: Optional[str]) -> Optional[SitemapShop]:
    products = list(state.get("analyzed") or [])
    origin = ""
    for item in products:
        url = str(item.get("url") or "")
        if url.startswith("http"):
            parsed = urlparse(url)
            origin = f"{parsed.scheme}://{parsed.netloc}"
            break
    origin = origin or (host or "").rstrip("/")
    records = []
    for item in products:
        url = str(item.get("url") or "")
        if not url:
            continue
        path = urlparse(url).path or url
        if not path.startswith("/"):
            path = "/" + path
        records.append(IndexRecord(path=path.rstrip("/") or "/", kind="product", indexable=False))
    if not records:
        return None
    return SitemapShop(
        platform=str(state.get("platform") or "odoo"),
        origin=origin,
        records=tuple(records),
        file_xml="<?xml version='1.0'?><urlset></urlset>",
    )


@router.get("/offer")
async def catalog_offer_status(
    license: Optional[str] = None,
    key: Optional[str] = None,
    x_aeo_license: Optional[str] = Header(default=None, alias="X-AEO-License"),
) -> Dict[str, Any]:
    ctx = await asyncio.to_thread(_context_cached, license, key, x_aeo_license)
    offer = ctx["offer"]
    return {
        "ok": True,
        "sale_order_name": ctx["order"],
        "general_allowed": ctx["consumed"].get("allowed") is True,
        "acquire_url": offer.get("acquire_url") or PRODUCT_URL,
        **offer,
    }


class CatalogStartRequest(BaseModel):
    batch: bool = False


class CatalogComposeRequest(BaseModel):
    product: Dict[str, Any]
    total: int = 0
    pending: List[Dict[str, Any]] = []
    block_index: int = 1
    origin: str = "https://arkiphere.cloud"
    injected: bool = False


class CatalogFeedRequest(BaseModel):
    products: List[Dict[str, Any]]
    total: Optional[int] = None
    origin: str = "https://arkiphere.cloud"


@router.post("/session")
async def catalog_session_start(
    body: Optional[CatalogStartRequest] = None,
    license: Optional[str] = None,
    key: Optional[str] = None,
    x_aeo_license: Optional[str] = Header(default=None, alias="X-AEO-License"),
) -> Dict[str, Any]:
    ctx = await asyncio.to_thread(_context_cached, license, key, x_aeo_license)
    if not ctx["license"]:
        raise HTTPException(status_code=400, detail="Falta la clave de activación.")
    batch = bool(body and body.batch)
    if not ctx["offer"]["owned"] and not batch:
        return {"ok": False, "reason": "optional", **ctx["offer"]}
    if not ctx["platforms"]:
        raise HTTPException(status_code=409, detail="Conecte primero la tienda en el asistente general.")
    shop = _shop(ctx["license"], ctx["platforms"][0])
    batch_ids = None
    if batch:
        if not hasattr(shop, "ensure_samples"):
            raise HTTPException(status_code=409, detail="Las ocho fichas nuevas están disponibles en Odoo.")
        batch_ids = shop.ensure_samples()
        shop = SelectedCatalogShop(shop, batch_ids)
    _invalidate_context(ctx["license"])
    return start_session(
        ctx["license"],
        shop,
        owned=True,
        locale=ctx["consumed"].get("lang") or "es",
        batch_ids=batch_ids,
    )


@router.post("/session/feed")
async def catalog_session_feed(
    body: CatalogFeedRequest,
    license: Optional[str] = None,
    key: Optional[str] = None,
    x_aeo_license: Optional[str] = Header(default=None, alias="X-AEO-License"),
) -> Dict[str, Any]:
    ctx = await asyncio.to_thread(_context_cached, license, key, x_aeo_license)
    if not ctx["license"]:
        raise HTTPException(status_code=400, detail="Falta la clave de activación.")
    if not body.products:
        raise HTTPException(status_code=400, detail="El bloque de catálogo está vacío.")
    rows = []
    for raw in body.products[:20]:
        row = normalize_odoo(raw, body.origin)
        if not row.get("url"):
            row["url"] = f"{body.origin.rstrip('/')}/shop/{row.get('id')}"
        if row.get("name") and row.get("url"):
            rows.append(row)
    if not rows:
        raise HTTPException(status_code=400, detail="Ninguna ficha del bloque tiene nombre y dirección.")
    backup = Path("/tmp/catalog-prod-baseline.json")
    backup.write_text(
        json.dumps({"origin": body.origin, "total": body.total, "products": body.products[:20]}, ensure_ascii=False),
        encoding="utf-8",
    )
    _invalidate_context(ctx["license"])
    return start_listed(ctx["license"], rows, locale=ctx["consumed"].get("lang") or "es", total=body.total)


@router.post("/compose")
async def catalog_compose(
    body: CatalogComposeRequest,
    license: Optional[str] = None,
    key: Optional[str] = None,
    x_aeo_license: Optional[str] = Header(default=None, alias="X-AEO-License"),
) -> Dict[str, Any]:
    ctx = await asyncio.to_thread(_context_cached, license, key, x_aeo_license)
    if not ctx["license"]:
        raise HTTPException(status_code=400, detail="Falta la clave de activación.")
    row = normalize_odoo(body.product, body.origin)
    if not row.get("url"):
        row["url"] = f"{body.origin.rstrip('/')}/shop/{row.get('id')}"
    if not row.get("name") or not row.get("url"):
        raise HTTPException(status_code=400, detail="La ficha necesita nombre y dirección.")
    if not run_public(ctx["license"]).get("total"):
        begin_run(ctx["license"], body.total)
    note_window(ctx["license"], body.pending or [row], row.get("id"), body.block_index)
    baseline = Path("/app/data/catalog-prod-baseline.jsonl")
    baseline.parent.mkdir(parents=True, exist_ok=True)
    with baseline.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps({"id": row.get("id"), "name": row.get("name"), "website_meta_title": body.product.get("website_meta_title") or "", "website_meta_description": body.product.get("website_meta_description") or "", "website_meta_keywords": body.product.get("website_meta_keywords") or ""}, ensure_ascii=False) + "\n")
    pack = build_pack(row, locale=ctx["consumed"].get("lang") or "es")
    pack = await with_model(pack, row, ctx["consumed"].get("lang") or "es")
    body_html = str(body.product.get("website_description") or "")
    if body_html in (False, "false"):
        body_html = ""
    values = native_values(pack, body_html)
    note_finished(ctx["license"], {"id": row.get("id"), "name": row.get("name"), "title": (pack.get("seo") or {}).get("title") or "", "source": pack.get("source") or "heuristic"}, False)
    return {"ok": True, "id": row.get("id"), "pack": pack, "values": values, "run": run_public(ctx["license"])}


@router.post("/injected")
async def catalog_injected(
    license: Optional[str] = None,
    key: Optional[str] = None,
    x_aeo_license: Optional[str] = Header(default=None, alias="X-AEO-License"),
) -> Dict[str, Any]:
    ctx = await asyncio.to_thread(_context_cached, license, key, x_aeo_license)
    if not ctx["license"]:
        raise HTTPException(status_code=400, detail="Falta la clave de activación.")
    return {"ok": True, "run": mark_injected(ctx["license"])}


@router.post("/tick")
async def catalog_session_tick(
    license: Optional[str] = None,
    key: Optional[str] = None,
    x_aeo_license: Optional[str] = Header(default=None, alias="X-AEO-License"),
) -> Dict[str, Any]:
    ctx = await asyncio.to_thread(_context_cached, license, key, x_aeo_license)
    if not ctx["license"]:
        raise HTTPException(status_code=400, detail="Falta la clave de activación.")
    if not get_session(ctx["license"]):
        raise HTTPException(status_code=409, detail="No hay un análisis de catálogo en curso.")
    before = len((get_session(ctx["license"]) or {}).get("analyzed") or [])
    snapshot = tick_session(ctx["license"])
    products = snapshot.get("products") or []
    if len(products) > before and products:
        current = products[-1]
        pack = await with_model(current.get("pack") or {}, current, ctx["consumed"].get("lang") or "es")
        remember_pack(ctx["license"], current.get("id"), pack, pack.get("source") or "heuristic")
        snapshot = public_session(ctx["license"])
    return snapshot


@router.get("/job")
async def catalog_job(
    license: Optional[str] = None,
    key: Optional[str] = None,
    x_aeo_license: Optional[str] = Header(default=None, alias="X-AEO-License"),
) -> Dict[str, Any]:
    ctx = await asyncio.to_thread(_context_cached, license, key, x_aeo_license)
    session = public_session(ctx["license"]) if ctx["license"] else {"ok": True, "tree": [], "queue": {"window": []}}
    general = connection_store.get_job(ctx["license"] or "") or {}
    return {
        "ok": True,
        "offer": ctx["offer"],
        "general": {
            "tree": general.get("tree") or [],
            "summary": general.get("summary"),
            "sale_order_name": general.get("sale_order_name") or ctx["order"],
            "host": general.get("host") or ctx["host"],
        },
        "catalog": session,
        "run": run_public(ctx["license"] or ""),
    }


@router.post("/publish")
async def catalog_publish(
    license: Optional[str] = None,
    key: Optional[str] = None,
    x_aeo_license: Optional[str] = Header(default=None, alias="X-AEO-License"),
) -> Dict[str, Any]:
    ctx = await asyncio.to_thread(_context_cached, license, key, x_aeo_license)
    if not ctx["license"]:
        raise HTTPException(status_code=400, detail="Falta la clave de activación.")
    state = get_session(ctx["license"])
    if not ctx["offer"]["owned"] and not (state or {}).get("batch_ids"):
        return {"ok": False, "reason": "optional", "written": []}
    if not state:
        raise HTTPException(status_code=409, detail="Analice el catálogo antes de publicar.")
    if ctx.get("metering_error"):
        raise HTTPException(
            status_code=503,
            detail="No se pudo leer el cupo de fichas del pedido. Inténtelo de nuevo.",
        )
    sitemap_shop = _sitemap_from_session(state, ctx["host"])
    result = publish_fixture(
        ctx["license"],
        sitemap_shop,
        host=ctx["host"],
        allowance=int(ctx.get("allowance") or 0),
    )
    rows, _err = _order_line_rows(ctx["order"])
    partner_id = (ctx.get("consumed") or {}).get("partner_id")
    meter_rows, partner_err = _partner_catalog_rows(partner_id, fallback_rows=rows)
    metering = _metering_for(
        ctx["license"],
        ctx["host"],
        meter_rows,
        source_error=_err or partner_err,
    )
    connection_store.record_apply(
        ctx["license"],
        {
            "ok": result.get("ok"),
            "platform": state.get("platform"),
            "message": "catalog fixture",
            "reason": result.get("reason"),
        },
    )
    _invalidate_context(ctx["license"])
    return {**result, **metering}


@router.post("/report.pdf")
async def catalog_report_pdf(
    license: Optional[str] = None,
    key: Optional[str] = None,
    x_aeo_license: Optional[str] = Header(default=None, alias="X-AEO-License"),
):
    ctx = await asyncio.to_thread(_context_cached, license, key, x_aeo_license)
    lic = ctx["license"] or ""
    session = get_session(lic) or {}
    if not report_ready(lic):
        raise HTTPException(
            status_code=409,
            detail="El informe solo se descarga cuando las fichas se han publicado en la tienda.",
        )
    dossier = {
        "locale": "es",
        "sale_order_name": ctx["order"] or "pedido",
        "host": (ctx["host"] or "sitio").replace("https://", "").replace("http://", ""),
        "complete": bool(session.get("done")),
        "products": list(session.get("analyzed") or []),
    }
    pdf = render_catalog_pdf(dossier)
    filename = f"informe-catalogo-{(dossier['sale_order_name'] or 'pedido').replace(' ', '')}-{dossier['host']}.pdf"
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
