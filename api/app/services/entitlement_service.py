"""Entitlement from Arkiphere confirmed sale.order (no payment gateways)."""
from __future__ import annotations

import json
import os
import threading
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional
from xmlrpc import client as xmlrpc_client

from app.config import settings

CONFIRMED_STATES = ("sale", "done")
PRODUCT_MARKERS = ("search engine optimizator", "optimizator")
_lock = threading.Lock()


def _store_path() -> str:
    return settings.ENTITLEMENT_STORE or "/app/data/entitlement.json"


def _load_store() -> Dict[str, Any]:
    path = _store_path()
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
            return data if isinstance(data, dict) else {"users": {}}
    except Exception:
        return {"users": {}}


def _save_store(data: Dict[str, Any]) -> None:
    path = _store_path()
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def _norm_login(value: Optional[str]) -> str:
    login = (value or settings.ENTITLEMENT_DEFAULT_LOGIN or "thedeployer777").strip()
    login = login.lstrip("@")
    return login or "thedeployer777"


def _is_optimizator_text(*parts: Any) -> bool:
    blob = " ".join(str(p or "") for p in parts).lower()
    return any(marker in blob for marker in PRODUCT_MARKERS)


def _odoo_password() -> Optional[str]:
    return (settings.ODOO_API_KEY or settings.ODOO_PASSWORD or "").strip() or None


def _odoo_execute(model: str, method: str, *args, **kwargs):
    password = _odoo_password()
    user = (settings.ODOO_USERNAME or "").strip()
    if not password or not user:
        return None
    base = (settings.ODOO_URL or "https://arkiphere.cloud").rstrip("/")
    common = xmlrpc_client.ServerProxy(f"{base}/xmlrpc/2/common", allow_none=True)
    uid = common.authenticate(settings.ODOO_DB or "osh", user, password, {})
    if not uid:
        raise RuntimeError("Odoo authentication failed")
    models = xmlrpc_client.ServerProxy(f"{base}/xmlrpc/2/object", allow_none=True)
    return models.execute_kw(settings.ODOO_DB or "osh", uid, password, model, method, list(args), kwargs or {})


def _odoo_find_partner(github_login: str) -> Optional[Dict[str, Any]]:
    domain = [
        "|",
        "|",
        "|",
        ("login", "=", github_login),
        ("login", "ilike", github_login),
        ("partner_id.name", "ilike", github_login),
        ("partner_id.email", "ilike", github_login),
    ]
    users = _odoo_execute(
        "res.users",
        "search_read",
        domain,
        fields=["id", "login", "partner_id", "name"],
        limit=5,
    )
    if users:
        u = users[0]
        partner = u.get("partner_id")
        partner_id = partner[0] if isinstance(partner, (list, tuple)) else partner
        partner_name = partner[1] if isinstance(partner, (list, tuple)) and len(partner) > 1 else u.get("name")
        return {"user_id": u.get("id"), "login": u.get("login"), "partner_id": partner_id, "partner_name": partner_name}
    partners = _odoo_execute(
        "res.partner",
        "search_read",
        ["|", ("name", "ilike", github_login), ("email", "ilike", github_login)],
        fields=["id", "name", "email"],
        limit=5,
    )
    if partners:
        p = partners[0]
        return {"user_id": None, "login": github_login, "partner_id": p["id"], "partner_name": p.get("name")}
    return None


def _odoo_orders_for_partner(partner_id: int) -> List[Dict[str, Any]]:
    orders = _odoo_execute(
        "sale.order",
        "search_read",
        [("partner_id", "=", partner_id)],
        fields=["id", "name", "state", "client_order_ref"],
        limit=40,
        order="id desc",
    ) or []
    if not orders:
        return []
    lines = _odoo_execute(
        "sale.order.line",
        "search_read",
        [("order_id", "in", [o["id"] for o in orders])],
        fields=["order_id", "name", "product_id"],
    ) or []
    by_order: Dict[int, List[str]] = {}
    for line in lines:
        oid = line.get("order_id")
        oid = oid[0] if isinstance(oid, (list, tuple)) else oid
        prod = line.get("product_id")
        prod_name = prod[1] if isinstance(prod, (list, tuple)) and len(prod) > 1 else ""
        by_order.setdefault(oid, []).append(" ".join(x for x in (line.get("name"), prod_name) if x))
    out = []
    for order in orders:
        texts = by_order.get(order["id"]) or []
        out.append(
            {
                "id": order["id"],
                "name": order.get("name"),
                "state": order.get("state"),
                "lines": texts,
                "optimizator": _is_optimizator_text(order.get("name"), order.get("client_order_ref"), *texts),
            }
        )
    return out


def _ledger_entry(github_login: str) -> Dict[str, Any]:
    with _lock:
        store = _load_store()
        users = store.setdefault("users", {})
        return dict(users.get(github_login) or {})


def register_confirmed(
    github_login: str,
    sale_order_name: str,
    partner_name: Optional[str] = None,
    source: str = "arkiphere",
) -> Dict[str, Any]:
    login = _norm_login(github_login)
    name = (sale_order_name or "").strip()
    if not name:
        raise ValueError("sale_order_name required")
    with _lock:
        store = _load_store()
        users = store.setdefault("users", {})
        entry = users.setdefault(login, {"orders": [], "partner_name": partner_name or login})
        orders = [o for o in (entry.get("orders") or []) if o.get("name") != name]
        orders.append(
            {
                "name": name,
                "state": "sale",
                "product": "Search Engine Optimizator",
                "source": source,
            }
        )
        entry["orders"] = orders
        if partner_name:
            entry["partner_name"] = partner_name
        users[login] = entry
        _save_store(store)
    return check(login)


def revoke(github_login: str, sale_order_name: Optional[str] = None) -> Dict[str, Any]:
    """Used for E2E blocked state: drop Optimizator ledger rows (does not cancel Arkiphere SOs)."""
    login = _norm_login(github_login)
    with _lock:
        store = _load_store()
        users = store.setdefault("users", {})
        entry = users.get(login) or {"orders": []}
        if sale_order_name:
            entry["orders"] = [o for o in (entry.get("orders") or []) if o.get("name") != sale_order_name]
        else:
            entry["orders"] = [
                o for o in (entry.get("orders") or []) if not _is_optimizator_text(o.get("name"), o.get("product"))
            ]
        users[login] = entry
        _save_store(store)
    return check(login)


def check(github_login: Optional[str] = None) -> Dict[str, Any]:
    login = _norm_login(github_login)
    partner: Dict[str, Any] = {"login": login, "partner_id": None, "partner_name": None}
    odoo_orders: List[Dict[str, Any]] = []
    odoo_error = None
    try:
        found = _odoo_find_partner(login) if _odoo_password() and settings.ODOO_USERNAME else None
        if found:
            partner = found
            odoo_orders = _odoo_orders_for_partner(int(found["partner_id"]))
    except Exception as exc:
        odoo_error = str(exc)[:240]

    ledger = _ledger_entry(login)
    ledger_orders = list(ledger.get("orders") or [])
    confirmed = []
    for order in odoo_orders:
        if order.get("state") in CONFIRMED_STATES and order.get("optimizator"):
            confirmed.append(order)
    for order in ledger_orders:
        if (order.get("state") in CONFIRMED_STATES) and _is_optimizator_text(order.get("name"), order.get("product")):
            if not any(c.get("name") == order.get("name") for c in confirmed):
                confirmed.append(order)

    if confirmed:
        chosen = confirmed[0]
        return {
            "allowed": True,
            "github_login": login,
            "partner_id": partner.get("partner_id"),
            "partner_name": partner.get("partner_name") or ledger.get("partner_name") or login,
            "sale_order_name": chosen.get("name"),
            "sale_order_state": chosen.get("state") or "sale",
            "message": f"Pedido confirmado {chosen.get('name')}. Puedes usar Search Engine Optimizator.",
            "cta_url": None,
            "cta_label": None,
            "odoo_error": odoo_error,
        }

    return {
        "allowed": False,
        "github_login": login,
        "partner_id": partner.get("partner_id"),
        "partner_name": partner.get("partner_name") or ledger.get("partner_name") or login,
        "sale_order_name": None,
        "sale_order_state": None,
        "message": "No hay un pedido confirmado de Search Engine Optimizator. Crea y confirma el pedido en Arkiphere para continuar.",
        "cta_url": settings.ARKIPHERE_SHOP_URL,
        "cta_label": "Crear o confirmar pedido en Arkiphere",
        "login_url": settings.ARKIPHERE_LOGIN_URL,
        "odoo_error": odoo_error,
    }


def _clean(value: Any) -> Any:
    if value is False or value is None or value == "":
        return None
    return value


def _blocked(key: Optional[str] = None, message: Optional[str] = None, error: Optional[str] = None) -> Dict[str, Any]:
    return {
        "allowed": False,
        "key": (key or "").strip() or None,
        "sale_order_name": None,
        "aeo_site_url": None,
        "partner_id": None,
        "github_login": None,
        "open_url": None,
        "message": message
        or "No hay un pedido confirmado de Search Engine Optimizator. Crea y confirma el pedido en Arkiphere para continuar.",
        "cta_url": settings.ARKIPHERE_SHOP_URL,
        "cta_label": "Crear o confirmar pedido en Arkiphere",
        "login_url": settings.ARKIPHERE_LOGIN_URL,
        "consume_error": error,
    }


def consume(key: Optional[str] = None, github_login: Optional[str] = None) -> Dict[str, Any]:
    """Forward to Arkiphere /aeo/license/consume/http. Does not decide entitlement locally."""
    license_key = (key or "").strip()
    if not license_key:
        return _blocked(message="Falta la clave de activación. Ábrela desde Arkiphere (Open AEO) o pégala aquí.")
    base = (getattr(settings, "ARKIPHERE_CONSUME_URL", None) or settings.ODOO_URL or "https://arkiphere.cloud").rstrip("/")
    login = (github_login or "").strip().lstrip("@") or None
    payload = {"key": license_key}
    if login:
        payload["github_login"] = login
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{base}/aeo/license/consume/http",
        data=body,
        headers={"Accept": "application/json", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw = json.loads(resp.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as exc:
        try:
            raw = json.loads(exc.read().decode("utf-8") or "{}")
        except Exception:
            return _blocked(license_key, error=f"Arkiphere HTTP {exc.code}")
    except Exception as exc:
        return _blocked(license_key, message="No pudimos comprobar el pedido ahora. Inténtalo de nuevo.", error=str(exc)[:240])

    if not isinstance(raw, dict):
        return _blocked(license_key, error="Respuesta inválida de Arkiphere")
    allowed = raw.get("allowed") is True
    sale_order_name = _clean(raw.get("sale_order_name"))
    site = _clean(raw.get("aeo_site_url"))
    if not allowed:
        return {
            **_blocked(license_key),
            "sale_order_name": sale_order_name,
            "aeo_site_url": site,
            "partner_id": _clean(raw.get("partner_id")),
            "github_login": _clean(raw.get("github_login")) or login,
            "open_url": _clean(raw.get("open_url")),
        }
    return {
        "allowed": True,
        "key": license_key,
        "sale_order_name": sale_order_name,
        "sale_order_state": "sale",
        "aeo_site_url": site,
        "partner_id": _clean(raw.get("partner_id")),
        "github_login": _clean(raw.get("github_login")) or login,
        "open_url": _clean(raw.get("open_url")),
        "message": f"Pedido confirmado {sale_order_name}. Puedes usar Search Engine Optimizator.",
        "cta_url": None,
        "cta_label": None,
        "login_url": settings.ARKIPHERE_LOGIN_URL,
        "consume_error": None,
    }
