from typing import Any, Dict, Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from app.services import arkiphere_connection, connection_store, schema_context
from app.services.odoo_inject import discover_database, probe_login
from app.services.site_guard import bind_license_site, extract_license, keep_https

router = APIRouter()

RECOMMENDATIONS = {
    "odoo": [
        {"id": "website", "label": "Sitio web Odoo", "why": "Hace falta para título, descripción y datos estructurados."},
        {"id": "xmlrpc", "label": "Usuario con API key", "why": "Así el Optimizator puede escribir el pack en tu tienda."},
    ],
    "prestashop": [
        {"id": "webservice", "label": "Webservice PrestaShop", "why": "Activa el webservice y pega la clave aquí."},
    ],
    "woocommerce": [
        {"id": "rest", "label": "REST WooCommerce", "why": "Clave y secreto de consumidor con permiso de escritura."},
    ],
}


class ConnectionBody(BaseModel):
    license: Optional[str] = None
    key: Optional[str] = None
    platform: str = Field(..., min_length=3)
    url: Optional[str] = None
    database: Optional[str] = None
    username: Optional[str] = None
    api_key: Optional[str] = None
    ws_key: Optional[str] = None
    consumer_key: Optional[str] = None
    consumer_secret: Optional[str] = None
    target: Optional[str] = None
    github_login: Optional[str] = None


class ConnectionRevoke(BaseModel):
    license: Optional[str] = None
    key: Optional[str] = None
    sale_order_name: Optional[str] = None
    github_login: Optional[str] = None
    platform: Optional[str] = None


def _license(header: Optional[str], body: Any) -> str:
    return extract_license(header, getattr(body, "license", None), getattr(body, "key", None))


@router.get("/status")
async def connection_status(
    license: Optional[str] = None,
    key: Optional[str] = None,
    x_aeo_license: Optional[str] = Header(default=None, alias="X-AEO-License"),
):
    lic = extract_license(x_aeo_license, license, key)
    bound = bind_license_site(lic, None)
    pack = connection_store.public_platforms(lic)
    return {
        "ok": True,
        "connected": bool(pack.get("connected")),
        "site_url": bound["bound_site_url"],
        "sale_order_name": bound.get("sale_order_name"),
        "connection": pack.get("connection"),
        "platforms": pack.get("platforms") or {},
        "platforms_list": list(connection_store.PLATFORMS),
        "recommendations": RECOMMENDATIONS,
    }


@router.post("/register")
async def connection_register(
    body: ConnectionBody,
    x_aeo_license: Optional[str] = Header(default=None, alias="X-AEO-License"),
):
    lic = _license(x_aeo_license, body)
    bound = bind_license_site(lic, body.url, github_login=body.github_login)
    platform = body.platform.strip().lower()
    if platform not in connection_store.PLATFORMS:
        raise HTTPException(status_code=400, detail=f"Plataforma no soportada. Usa: {', '.join(connection_store.PLATFORMS)}")
    site = bound["bound_site_url"]
    if platform == "odoo" and not (body.api_key and body.username):
        raise HTTPException(status_code=400, detail="Para Odoo hace falta usuario y clave API.")
    database = (body.database or "").strip()
    if platform == "odoo":
        if not database:
            database = discover_database(site)
        probe = probe_login(site, database, body.username or "", body.api_key or "")
        if not probe.get("ok"):
            raise HTTPException(status_code=400, detail=probe.get("message") or "No se pudo conectar con Odoo.")
    if platform == "prestashop" and not body.ws_key:
        raise HTTPException(status_code=400, detail="Para PrestaShop hace falta la clave del webservice.")
    if platform == "woocommerce" and not (body.consumer_key and body.consumer_secret):
        raise HTTPException(status_code=400, detail="Para WooCommerce hacen falta clave y secreto de consumidor.")
    snap = await schema_context.snapshot(site)
    ark = await arkiphere_connection.save_to_order_line(
        {
            "key": lic,
            "platform": platform,
            "url": site,
            "database": database or body.database,
            "username": body.username,
            "api_key": body.api_key,
            "ws_key": body.ws_key,
            "consumer_key": body.consumer_key,
            "consumer_secret": body.consumer_secret,
            "sale_order_name": bound.get("sale_order_name"),
        }
    )
    stored = connection_store.upsert(
        lic,
        {
            "platform": platform,
            "url": site,
            "host": bound.get("bound_host"),
            "database": database or body.database,
            "username": body.username,
            "api_key": body.api_key,
            "ws_key": body.ws_key,
            "consumer_key": body.consumer_key,
            "consumer_secret": body.consumer_secret,
            "target": body.target,
            "sale_order_name": bound.get("sale_order_name"),
            "arkiphere": {
                "ok": True,
                "mode": ark.get("mode") if ark.get("ok") else "local",
                "sale_line_id": ark.get("sale_line_id"),
                "written": ark.get("written"),
                "message": None if (not ark.get("ok") or "xmlrpc" in str(ark.get("message") or "").lower() or "XML-RPC" in str(ark.get("message") or "")) else ark.get("message"),
            },
            "schema_snapshot": {
                "host": snap.get("host"),
                "title": snap.get("title"),
                "h1": snap.get("h1"),
                "schema_types": snap.get("schema_types"),
                "internal_links": snap.get("internal_links"),
                "ok": snap.get("ok"),
            },
            "recommendations": RECOMMENDATIONS.get(platform) or [],
        },
    )
    pack = connection_store.public_platforms(lic)
    return {
        "ok": True,
        "connected": True,
        "site_url": site,
        "sale_order_name": bound.get("sale_order_name"),
        "connection": stored,
        "platforms": pack.get("platforms") or {},
        "arkiphere": ark,
        "schema_snapshot": snap,
        "message": (
            "Conexión guardada en el pedido Arkiphere."
            if ark.get("ok")
            else "Conexión guardada aquí. Arkiphere aún no confirmó la línea de pedido."
        ),
    }


@router.post("/revoke")
async def connection_revoke(
    body: ConnectionRevoke,
    x_aeo_license: Optional[str] = Header(default=None, alias="X-AEO-License"),
):
    lic = _license(x_aeo_license, body)
    if not lic and not body.sale_order_name:
        raise HTTPException(status_code=400, detail="Falta la clave o el pedido.")
    sale_name = body.sale_order_name
    if lic:
        try:
            bound = bind_license_site(lic, None, github_login=body.github_login)
            sale_name = sale_name or bound.get("sale_order_name")
        except HTTPException:
            pass
    platform = str(body.platform or "").strip().lower() or None
    local = connection_store.revoke(lic, sale_order_name=sale_name, platform=platform)
    ark = {"ok": True, "skipped": True}
    if not local.get("remaining_connected"):
        ark = await arkiphere_connection.revoke_order_line({"key": lic, "sale_order_name": sale_name})
    pack = connection_store.public_platforms(lic) if lic else {"platforms": {}, "connection": None, "connected": False}
    return {
        "ok": True,
        "revoked": local.get("revoked"),
        "platform": local.get("platform"),
        "remaining_connected": local.get("remaining_connected"),
        "connection": pack.get("connection"),
        "platforms": pack.get("platforms") or {},
        "arkiphere": ark,
        "message": "Conexión revocada en el Optimizator y en la línea de pedido."
        if not local.get("remaining_connected")
        else f"Conexión {local.get('platform') or ''} revocada. Las demás plataformas siguen activas.",
    }
