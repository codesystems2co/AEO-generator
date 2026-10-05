"""Catalog ficha metering: allowance from product 110 qty, persist applied IDs.

«Processed» means successfully applied/written under (license, hostname) —
not merely analyzed. Re-apply of an already-processed ID costs 0.
"""
from __future__ import annotations

import json
import os
import threading
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set
from urllib.parse import urlparse

from app.services.catalog_product import PRODUCT_URL

CATALOG_TMPL_ID = 110
CATALOG_MARKER = "product catalog aeo and seo pack with ia"
_lock = threading.Lock()


def _store_path() -> str:
    try:
        from app.config import settings

        path = getattr(settings, "CATALOG_METERING_STORE", None)
        if path:
            return str(path)
    except Exception:
        pass
    return os.environ.get("CATALOG_METERING_STORE") or "/app/data/catalog_metering.json"


def _load_store() -> Dict[str, Any]:
    path = _store_path()
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
            if isinstance(data, dict):
                sites = data.get("sites")
                if not isinstance(sites, dict):
                    data["sites"] = {}
                return data
    except Exception:
        pass
    return {"sites": {}}


def _save_store(data: Dict[str, Any]) -> None:
    path = _store_path()
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def normalize_host(value: Optional[str]) -> str:
    text = (value or "").strip()
    if not text:
        return ""
    if "://" not in text:
        text = "https://" + text
    try:
        host = urlparse(text).hostname or ""
    except Exception:
        host = text
    return host.lower().removeprefix("www.")


def _site_key(license_key: str, host: Optional[str]) -> str:
    return f"{(license_key or '').strip()}|{normalize_host(host)}"


def _product_token(product_id: Any) -> str:
    return str(product_id).strip()


def _name_blob(row: Dict[str, Any]) -> str:
    product = row.get("product_id")
    product_name = ""
    if isinstance(product, (list, tuple)) and len(product) > 1:
        product_name = str(product[1] or "")
    parts = [
        row.get("name"),
        product_name,
        row.get("default_code"),
        row.get("product_default_code"),
    ]
    return " ".join(str(part or "") for part in parts).lower()


def _template_id(row: Dict[str, Any]) -> Optional[int]:
    for key in ("product_template_id", "product_tmpl_id"):
        value = row.get(key)
        if isinstance(value, (list, tuple)) and value:
            try:
                return int(value[0])
            except (TypeError, ValueError):
                return None
        if isinstance(value, int):
            return value
        if isinstance(value, str) and value.isdigit():
            return int(value)
    product = row.get("product_id")
    if isinstance(product, (list, tuple)) and product:
        # Display name sometimes embeds tmpl id; prefer explicit fields above.
        return None
    return None


def is_catalog_line(row: Dict[str, Any]) -> bool:
    if not isinstance(row, dict):
        return False
    if CATALOG_MARKER in _name_blob(row):
        return True
    tmpl = _template_id(row)
    if tmpl == CATALOG_TMPL_ID:
        return True
    code = str(row.get("default_code") or row.get("product_default_code") or "").strip().lower()
    if code in {str(CATALOG_TMPL_ID), "catalog-aeo", "aeo-catalog"}:
        return True
    return False


def line_host(row: Dict[str, Any]) -> str:
    for key in ("aeo_site_url", "aeo_connect_shop_url", "host", "site"):
        host = normalize_host(row.get(key) if isinstance(row, dict) else None)
        if host:
            return host
    return ""


def allowance_from_rows(
    rows: Sequence[Dict[str, Any]],
    host: Optional[str] = None,
) -> int:
    """Sum catalog product-110 qty on confirmed lines.

    When ``host`` is set, only lines whose ``aeo_site_url`` matches that
    session hostname count. Unbound catalog lines (no hostname) do not
    credit a connected shop — that was the S00734 gap.
    """
    catalog = [dict(row) for row in rows if is_catalog_line(row)]
    if not catalog:
        return 0
    wanted = normalize_host(host)
    if wanted:
        catalog = [row for row in catalog if line_host(row) == wanted]
    total = 0.0
    for row in catalog:
        try:
            total += float(row.get("product_uom_qty") or 0)
        except (TypeError, ValueError):
            continue
    return max(0, int(total))


def processed_ids(license_key: str, host: Optional[str]) -> Set[str]:
    key = _site_key(license_key, host)
    with _lock:
        store = _load_store()
        site = store.get("sites", {}).get(key) or {}
        ids = site.get("processed_ids") or []
        return {str(item) for item in ids if str(item).strip()}


def is_processed(license_key: str, host: Optional[str], product_id: Any) -> bool:
    token = _product_token(product_id)
    if not token:
        return False
    return token in processed_ids(license_key, host)


def used_count(license_key: str, host: Optional[str]) -> int:
    return len(processed_ids(license_key, host))


def remaining(license_key: str, host: Optional[str], allowance: int) -> int:
    return max(0, int(allowance or 0) - used_count(license_key, host))


def can_apply_new(
    license_key: str,
    host: Optional[str],
    product_id: Any,
    allowance: int,
) -> bool:
    """True if write is free (already processed) or a new credit remains."""
    if is_processed(license_key, host, product_id):
        return True
    return remaining(license_key, host, allowance) > 0


def record_applied(license_key: str, host: Optional[str], product_id: Any) -> bool:
    """Persist a newly applied product id. Returns True if it was new."""
    token = _product_token(product_id)
    lic = (license_key or "").strip()
    if not token or not lic:
        return False
    key = _site_key(lic, host)
    with _lock:
        store = _load_store()
        sites = store.setdefault("sites", {})
        site = dict(sites.get(key) or {})
        current: List[str] = [str(item) for item in (site.get("processed_ids") or []) if str(item).strip()]
        if token in current:
            return False
        site = {
            **site,
            "license": lic,
            "host": normalize_host(host),
            "processed_ids": current + [token],
        }
        sites[key] = site
        _save_store(store)
        return True


def compute_needed_qty(
    catalog_total: int,
    license_key: str,
    host: Optional[str],
    allowance: int,
) -> int:
    """Fichas to buy = unmet NEW catalog IDs beyond remaining allowance.

    neededQty = max(0, (catalogTotal − processed/applied) − remaining).
    Re-runs of already-processed IDs are free and must not inflate buy qty.
    """
    total = max(0, int(catalog_total or 0))
    used = used_count(license_key, host)
    allow = max(0, int(allowance or 0))
    left = max(0, allow - used)
    return max(0, total - used - left)


def metering_snapshot(
    license_key: str,
    host: Optional[str],
    allowance: int,
    *,
    needed_qty: Optional[int] = None,
    catalog_total: Optional[int] = None,
) -> Dict[str, Any]:
    from app.services.catalog_product import catalog_product_url

    used = used_count(license_key, host)
    allow = max(0, int(allowance or 0))
    left = max(0, allow - used)
    qty = needed_qty
    if qty is None and catalog_total is not None:
        qty = compute_needed_qty(catalog_total, license_key, host, allow)
    if qty is None:
        qty = left if left > 0 else 1
    out = {
        "allowance": allow,
        "used": used,
        "remaining": left,
        "processed_ids": used,
        "acquire_url": catalog_product_url(False, host=host, quantity=qty) or PRODUCT_URL,
    }
    if catalog_total is not None:
        out["catalog_total"] = max(0, int(catalog_total))
    if catalog_total is not None or needed_qty is not None:
        out["needed_qty"] = max(0, int(qty or 0))
    return out


def filter_new_ids(
    license_key: str,
    host: Optional[str],
    product_ids: Iterable[Any],
) -> List[str]:
    known = processed_ids(license_key, host)
    out: List[str] = []
    for item in product_ids:
        token = _product_token(item)
        if token and token not in known and token not in out:
            out.append(token)
    return out
