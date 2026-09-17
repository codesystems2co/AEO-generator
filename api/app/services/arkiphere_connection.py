"""Push/revoke connection fields onto the Arkiphere Optimizator sale.order.line."""
from __future__ import annotations

import json
from typing import Any, Dict, Optional
from xmlrpc import client as xmlrpc_client

import httpx

from app.config import settings
from app.services.entitlement_service import _odoo_execute, _odoo_password

SAVE_PATHS = (
    "/aeo/connection/http",
    "/aeo/license/connection/http",
    "/aeo/order/connection/http",
)
REVOKE_PATHS = (
    "/aeo/connection/revoke/http",
    "/aeo/license/connection/revoke/http",
    "/aeo/order/connection/revoke/http",
)

LINE_FIELDS = (
    "aeo_platform",
    "aeo_conn_platform",
    "aeo_conn_url",
    "aeo_conn_db",
    "aeo_conn_user",
    "aeo_conn_secret",
    "aeo_connection_json",
    "x_aeo_platform",
    "x_aeo_conn_url",
)


def _base() -> str:
    return (getattr(settings, "ARKIPHERE_CONSUME_URL", None) or settings.ODOO_URL or "https://arkiphere.cloud").rstrip("/")


def _public_payload(body: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "key": body.get("key"),
        "platform": body.get("platform"),
        "url": body.get("url"),
        "database": body.get("database"),
        "username": body.get("username"),
        "api_key": body.get("api_key") or None,
        "ws_key": body.get("ws_key") or None,
        "consumer_key": body.get("consumer_key") or None,
        "consumer_secret": body.get("consumer_secret") or None,
        "sale_order_name": body.get("sale_order_name"),
    }


async def _post_first(paths, payload: Dict[str, Any]) -> Dict[str, Any]:
    base = _base()
    attempts = []
    timeout = httpx.Timeout(20.0, connect=6.0)
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        for path in paths:
            url = f"{base}{path}"
            attempt: Dict[str, Any] = {"url": url}
            try:
                r = await client.post(url, json=payload, headers={"Accept": "application/json"})
                attempt["status_code"] = r.status_code
                try:
                    data = r.json()
                except Exception:
                    data = {"raw": (r.text or "")[:400]}
                attempt["body"] = data if not isinstance(data, dict) else {k: data.get(k) for k in list(data)[:12]}
                if r.status_code == 404:
                    attempts.append(attempt)
                    continue
                ok = 200 <= r.status_code < 300 and (
                    not isinstance(data, dict) or data.get("ok") is not False and data.get("allowed") is not False
                )
                if isinstance(data, dict) and data.get("ok") is False:
                    ok = False
                return {
                    "ok": ok,
                    "forwarded": True,
                    "path": path,
                    "status_code": r.status_code,
                    "data": data if isinstance(data, dict) else {"raw": data},
                    "attempts": attempts + [attempt],
                }
            except Exception as exc:
                attempt["error"] = str(exc)[:200]
                attempts.append(attempt)
    return {
        "ok": False,
        "forwarded": False,
        "path": None,
        "status_code": None,
        "data": None,
        "message": "Arkiphere todavía no expone /aeo/connection/http. Se guarda el espejo local.",
        "attempts": attempts,
    }


def _line_write_vals(body: Dict[str, Any], clear: bool = False) -> Dict[str, Any]:
    if clear:
        return {
            "aeo_connect_platform": False,
            "aeo_connect_shop_url": False,
            "aeo_connect_database": False,
            "aeo_connect_login": False,
            "aeo_connect_rpc_url": False,
            "aeo_connect_state": "revoked",
            "aeo_connect_has_secret": False,
            "aeo_platform": False,
            "aeo_conn_platform": False,
            "aeo_conn_url": False,
            "aeo_conn_db": False,
            "aeo_conn_user": False,
            "aeo_conn_secret": False,
            "aeo_connection_json": False,
        }
    blob = json.dumps(
        {
            "platform": body.get("platform"),
            "url": body.get("url"),
            "database": body.get("database"),
            "username": body.get("username"),
            "has_api_key": bool(body.get("api_key")),
            "has_ws_key": bool(body.get("ws_key")),
            "has_consumer": bool(body.get("consumer_key") or body.get("consumer_secret")),
        },
        ensure_ascii=False,
    )
    return {
        "aeo_connect_platform": body.get("platform"),
        "aeo_connect_shop_url": body.get("url"),
        "aeo_connect_database": body.get("database"),
        "aeo_connect_login": body.get("username"),
        "aeo_connect_rpc_url": f"{(body.get('url') or '').rstrip('/')}/xmlrpc/2/object" if body.get("url") else False,
        "aeo_connect_state": "registered",
        "aeo_connect_has_secret": True,
        "aeo_platform": body.get("platform"),
        "aeo_conn_platform": body.get("platform"),
        "aeo_conn_url": body.get("url"),
        "aeo_conn_db": body.get("database"),
        "aeo_conn_user": body.get("username"),
        "aeo_conn_secret": body.get("api_key") or body.get("ws_key") or body.get("consumer_secret"),
        "aeo_connection_json": blob,
    }


def _xmlrpc_write_line(body: Dict[str, Any], clear: bool = False) -> Dict[str, Any]:
    if not _odoo_password() or not (settings.ODOO_USERNAME or "").strip():
        return {"ok": False, "mode": "xmlrpc", "message": "Odoo XML-RPC no configurado en el generador."}
    order_name = (body.get("sale_order_name") or "").strip()
    if not order_name:
        return {"ok": False, "mode": "xmlrpc", "message": "Falta el pedido para escribir la línea."}
    try:
        orders = _odoo_execute(
            "sale.order",
            "search_read",
            [("name", "=", order_name)],
            fields=["id", "name"],
            limit=1,
        ) or []
        if not orders:
            return {"ok": False, "mode": "xmlrpc", "message": f"Pedido {order_name} no encontrado."}
        oid = orders[0]["id"]
        lines = _odoo_execute(
            "sale.order.line",
            "search_read",
            [("order_id", "=", oid)],
            fields=["id", "name", "product_id"],
            limit=40,
        ) or []
        chosen = None
        for line in lines:
            blob = " ".join(
                str(x or "")
                for x in (
                    line.get("name"),
                    (line.get("product_id") or [None, ""])[1] if isinstance(line.get("product_id"), (list, tuple)) else "",
                )
            ).lower()
            if "optimizator" in blob or "aeo" in blob:
                chosen = line
                break
        if not chosen and lines:
            chosen = lines[0]
        if not chosen:
            return {"ok": False, "mode": "xmlrpc", "message": "No hay línea de pedido Optimizator."}
        vals = _line_write_vals(body, clear=clear)
        fields = _odoo_execute("sale.order.line", "fields_get", attributes=["type"]) or {}
        usable = {k: v for k, v in vals.items() if k in fields}
        if not usable:
            return {
                "ok": False,
                "mode": "xmlrpc",
                "sale_line_id": chosen["id"],
                "message": "La línea no tiene campos aeo_conn_* todavía (addon CE pendiente).",
                "available_hint": [k for k in LINE_FIELDS if k in fields],
            }
        _odoo_execute("sale.order.line", "write", [chosen["id"]], usable)
        return {
            "ok": True,
            "mode": "xmlrpc",
            "sale_order_name": order_name,
            "sale_line_id": chosen["id"],
            "written": list(usable.keys()),
        }
    except xmlrpc_client.Fault as exc:
        return {"ok": False, "mode": "xmlrpc", "message": str(exc)[:240]}
    except Exception as exc:
        return {"ok": False, "mode": "xmlrpc", "message": str(exc)[:240]}


async def save_to_order_line(body: Dict[str, Any]) -> Dict[str, Any]:
    http = await _post_first(SAVE_PATHS, _public_payload(body))
    if http.get("ok"):
        data = http.get("data") or {}
        return {
            "ok": True,
            "mode": "http",
            "path": http.get("path"),
            "sale_order_name": data.get("sale_order_name") or body.get("sale_order_name"),
            "sale_line_id": data.get("sale_line_id"),
            "platform": body.get("platform"),
            "url": body.get("url"),
            "has_secrets": True,
            "data": {k: data.get(k) for k in ("ok", "sale_order_name", "sale_line_id", "platform", "url") if k in data},
        }
    rpc = _xmlrpc_write_line(body, clear=False)
    if rpc.get("ok"):
        return rpc
    return {
        "ok": False,
        "mode": "pending",
        "http": {"forwarded": http.get("forwarded"), "path": http.get("path"), "status_code": http.get("status_code"), "message": http.get("message")},
        "xmlrpc": rpc,
        "message": http.get("message") or rpc.get("message") or "No se pudo escribir la línea de pedido.",
    }


async def revoke_order_line(body: Dict[str, Any]) -> Dict[str, Any]:
    payload = {"key": body.get("key"), "sale_order_name": body.get("sale_order_name")}
    http = await _post_first(REVOKE_PATHS, payload)
    rpc = _xmlrpc_write_line(body, clear=True)
    return {
        "ok": bool(http.get("ok") or rpc.get("ok") or not http.get("forwarded")),
        "http": {"ok": http.get("ok"), "path": http.get("path"), "status_code": http.get("status_code")},
        "xmlrpc": rpc,
    }
