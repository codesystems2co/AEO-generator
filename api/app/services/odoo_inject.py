"""Direct Odoo website SEO write when Core is down and the customer typed RPC details.

Epic #27 / #28 / #29:
- SEO pack: only website_meta_* (never name, body, price, or other scalars).
- Never fall back to the first published page when the target URL is missing.
- AEO pack: append/refresh <!-- AEO:START v1 --> … <!-- AEO:END --> on product.template
  website_description only.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from urllib.parse import urlparse
from xmlrpc import client as xmlrpc_client

from app.services.aeo_block import detect_injection, merge_block, render_faq_html, strip_block


def _auth(url: str, database: str, username: str, api_key: str):
    base = (url or "").rstrip("/")
    common = xmlrpc_client.ServerProxy(f"{base}/xmlrpc/2/common", allow_none=True)
    uid = common.authenticate(database, username, api_key, {})
    if not uid:
        raise RuntimeError("Odoo authentication failed")
    models = xmlrpc_client.ServerProxy(f"{base}/xmlrpc/2/object", allow_none=True)
    return uid, models


def discover_database(url: str) -> str:
    base = (url or "").rstrip("/")
    if not base:
        return ""
    listed = []
    try:
        dbproxy = xmlrpc_client.ServerProxy(f"{base}/xmlrpc/2/db", allow_none=True)
        listed = [str(name).strip() for name in (dbproxy.list() or []) if str(name).strip()]
    except Exception:
        listed = []
    if len(listed) == 1:
        return listed[0]
    try:
        from app.config import settings

        host = urlparse(base).netloc
        own = urlparse((settings.ODOO_URL or "").strip()).netloc
        fallback = (settings.ODOO_DB or "").strip()
        if host and host == own and fallback:
            return fallback
    except Exception:
        return ""
    return ""


def auth_failure_message(username: str, api_key: str) -> str:
    if (username or "").strip() and (username or "").strip() == (api_key or "").strip():
        return (
            "Odoo rechazó el acceso. La contraseña guardada es igual al usuario. "
            "Vuelva a conectar la tienda con la clave API de Odoo."
        )
    return "Odoo rechazó el usuario o la clave. Use contraseña de admin o clave API de Odoo."


def probe_login(url: str, database: str, username: str, api_key: str) -> Dict[str, Any]:
    if not ((url or "").strip() and (database or "").strip() and (username or "").strip() and (api_key or "").strip()):
        return {"ok": False, "message": "Faltan base, usuario o clave (contraseña o API key) de Odoo."}
    import socket

    previous = socket.getdefaulttimeout()
    socket.setdefaulttimeout(10)
    try:
        uid, _ = _auth(url, database, username, api_key)
        return {"ok": True, "uid": uid, "message": "Conexión con Odoo correcta."}
    except RuntimeError as exc:
        if "authentication" in str(exc).lower():
            return {"ok": False, "message": auth_failure_message(username, api_key)}
        return {"ok": False, "message": "No se pudo conectar con Odoo. Revisa base, usuario y contraseña."}
    except OSError:
        host = (url or "").strip() or "la tienda"
        return {
            "ok": False,
            "message": f"El generador no alcanza {host}. La base, el usuario y la contraseña no se han comprobado.",
        }
    except Exception:
        return {"ok": False, "message": "No se pudo conectar con Odoo. Revisa base, usuario y contraseña."}
    finally:
        socket.setdefaulttimeout(previous)


def _connection_parts(connection: Dict[str, Any]) -> Dict[str, str]:
    url = (connection.get("url") or "").strip()
    database = (connection.get("database") or "").strip() or discover_database(url)
    username = (connection.get("username") or "").strip()
    api_key = (connection.get("api_key") or "").strip()
    return {"url": url, "database": database, "username": username, "api_key": api_key}


def _target_path(target: Optional[str]) -> str:
    if not target:
        return ""
    if target.startswith("/"):
        return target
    try:
        parsed = urlparse(target if "://" in target else f"https://x{target}")
        return parsed.path or "/"
    except Exception:
        return ""


def inject_website_seo(connection: Dict[str, Any], seo: Dict[str, Any], target: Optional[str] = None) -> Dict[str, Any]:
    """SEO pack only: write website_meta_* on the matching website.page. No body overwrite."""
    parts = _connection_parts(connection)
    url, database, username, api_key = parts["url"], parts["database"], parts["username"], parts["api_key"]
    if not (url and database and username and api_key):
        return {
            "ok": False,
            "mode": "odoo-xmlrpc",
            "database": database or None,
            "message": "Faltan URL, base, usuario o clave API de Odoo.",
        }
    title = (seo.get("title") or "").strip()
    meta = (seo.get("meta_description") or "").strip()
    keywords = seo.get("keywords") or []
    if isinstance(keywords, list):
        kw = ", ".join(str(k) for k in keywords if k)
    else:
        kw = str(keywords or "")
    path = _target_path(target)
    if not path:
        return {
            "ok": False,
            "mode": "odoo-xmlrpc",
            "database": database,
            "message": "Destino no encontrado: falta la URL o ruta de la página. No se usó un registro por defecto.",
        }
    try:
        uid, models = _auth(url, database, username, api_key)
    except RuntimeError as exc:
        message = auth_failure_message(username, api_key) if "authentication" in str(exc).lower() else str(exc)[:240]
        return {"ok": False, "mode": "odoo-xmlrpc", "database": database, "message": message}
    except Exception as exc:
        return {"ok": False, "mode": "odoo-xmlrpc", "database": database, "message": str(exc)[:240]}

    def execute(model: str, method: str, *args, **kwargs):
        return models.execute_kw(database, uid, api_key, model, method, list(args), kwargs or {})
    try:
        pages = execute(
            "website.page",
            "search_read",
            ["|", ("url", "=", path), ("url", "=", path.rstrip("/") or "/")],
            fields=["id", "url", "name", "website_meta_title", "website_meta_description", "is_published"],
            limit=5,
        ) or []
        # #28: never fall back to the first published page.
        if not pages:
            return {
                "ok": False,
                "mode": "odoo-xmlrpc",
                "database": database,
                "message": f"Destino no encontrado: no hay website.page con url={path}.",
            }
        page = pages[0]
        vals = {}
        fields = execute("website.page", "fields_get", attributes=["type"]) or {}
        if title and "website_meta_title" in fields:
            vals["website_meta_title"] = title[:70]
        if meta and "website_meta_description" in fields:
            vals["website_meta_description"] = meta[:160]
        if kw and "website_meta_keywords" in fields:
            vals["website_meta_keywords"] = kw[:200]
        if not vals:
            return {
                "ok": False,
                "mode": "odoo-xmlrpc",
                "database": database,
                "page_id": page.get("id"),
                "message": "website.page no expone campos SEO en esta instancia.",
            }
        execute("website.page", "write", [page["id"]], vals)
        verify = execute(
            "website.page",
            "read",
            [page["id"]],
            fields=["id", "url", "website_meta_title", "website_meta_description"],
        ) or []
        row = verify[0] if verify else {}
        title_ok = bool(title) and title[:40] in (row.get("website_meta_title") or "")
        meta_ok = bool(meta) and meta[:40] in (row.get("website_meta_description") or "")
        return {
            "ok": True,
            "mode": "odoo-xmlrpc",
            "pack": "seo",
            "database": database,
            "page_id": page.get("id"),
            "page_url": row.get("url") or page.get("url"),
            "written": list(vals.keys()),
            "verify": {
                "website_meta_title": row.get("website_meta_title"),
                "website_meta_description": row.get("website_meta_description"),
                "title_ok": title_ok or bool(row.get("website_meta_title")),
                "meta_ok": meta_ok or bool(row.get("website_meta_description")),
            },
        }
    except xmlrpc_client.Fault as exc:
        return {"ok": False, "mode": "odoo-xmlrpc", "database": database, "message": str(exc)[:240]}
    except Exception as exc:
        return {"ok": False, "mode": "odoo-xmlrpc", "database": database, "message": str(exc)[:240]}


def inject_product_aeo(
    connection: Dict[str, Any],
    product_id: int,
    faq: Optional[List[Dict[str, str]]] = None,
    schema: Optional[Dict[str, Any]] = None,
    block_html: Optional[str] = None,
) -> Dict[str, Any]:
    """AEO pack: append/refresh the quote block on product.template.website_description."""
    parts = _connection_parts(connection)
    url, database, username, api_key = parts["url"], parts["database"], parts["username"], parts["api_key"]
    if not (url and database and username and api_key):
        return {"ok": False, "mode": "odoo-xmlrpc", "message": "Faltan URL, base, usuario o clave API de Odoo."}
    if not product_id:
        return {"ok": False, "mode": "odoo-xmlrpc", "message": "Destino no encontrado: falta el id del producto."}
    try:
        uid, models = _auth(url, database, username, api_key)
    except Exception as exc:
        return {"ok": False, "mode": "odoo-xmlrpc", "database": database, "message": str(exc)[:240]}

    def execute(model: str, method: str, *args, **kwargs):
        return models.execute_kw(database, uid, api_key, model, method, list(args), kwargs or {})

    try:
        rows = execute(
            "product.template",
            "read",
            [int(product_id)],
            fields=["id", "name", "list_price", "website_description", "website_meta_title"],
        ) or []
        if not rows:
            return {
                "ok": False,
                "mode": "odoo-xmlrpc",
                "database": database,
                "message": f"Destino no encontrado: product.template id={product_id}.",
            }
        row = rows[0]
        before_body = row.get("website_description") or ""
        detection = detect_injection(before_body)
        html_block = (block_html or "").strip() or render_faq_html(faq or [], schema)
        after_body = merge_block(before_body, html_block)
        # Never touch name / price / other scalars — only website_description.
        # execute() wraps *args into execute_kw args list — pass ids and vals as separate args.
        execute("product.template", "write", [int(product_id)], {"website_description": after_body})
        verify = execute(
            "product.template",
            "read",
            [int(product_id)],
            fields=["id", "name", "list_price", "website_description"],
        ) or []
        after = verify[0] if verify else {}
        name_ok = after.get("name") == row.get("name")
        price_ok = after.get("list_price") == row.get("list_price")
        return {
            "ok": bool(name_ok and price_ok and "AEO:START v1" in (after.get("website_description") or "")),
            "mode": "odoo-xmlrpc",
            "pack": "aeo",
            "database": database,
            "product_id": product_id,
            "detection": detection,
            "written": ["website_description"],
            "verify": {
                "name_ok": name_ok,
                "price_ok": price_ok,
                "block_present": "AEO:START v1" in (after.get("website_description") or ""),
            },
        }
    except xmlrpc_client.Fault as exc:
        return {"ok": False, "mode": "odoo-xmlrpc", "database": database, "message": str(exc)[:240]}
    except Exception as exc:
        return {"ok": False, "mode": "odoo-xmlrpc", "database": database, "message": str(exc)[:240]}


def rollback_product_aeo(connection: Dict[str, Any], product_id: int) -> Dict[str, Any]:
    """Remove the AEO markers block; leave the client's description untouched."""
    parts = _connection_parts(connection)
    url, database, username, api_key = parts["url"], parts["database"], parts["username"], parts["api_key"]
    if not (url and database and username and api_key):
        return {"ok": False, "mode": "odoo-xmlrpc", "message": "Faltan URL, base, usuario o clave API de Odoo."}
    if not product_id:
        return {"ok": False, "mode": "odoo-xmlrpc", "message": "Destino no encontrado: falta el id del producto."}
    try:
        uid, models = _auth(url, database, username, api_key)
    except Exception as exc:
        return {"ok": False, "mode": "odoo-xmlrpc", "database": database, "message": str(exc)[:240]}

    def execute(model: str, method: str, *args, **kwargs):
        return models.execute_kw(database, uid, api_key, model, method, list(args), kwargs or {})

    try:
        rows = execute(
            "product.template",
            "read",
            [int(product_id)],
            fields=["id", "name", "list_price", "website_description"],
        ) or []
        if not rows:
            return {
                "ok": False,
                "mode": "odoo-xmlrpc",
                "database": database,
                "message": f"Destino no encontrado: product.template id={product_id}.",
            }
        row = rows[0]
        before_body = row.get("website_description") or ""
        detection = detect_injection(before_body)
        if not detection.get("injected"):
            return {
                "ok": True,
                "mode": "odoo-xmlrpc",
                "pack": "aeo-rollback",
                "database": database,
                "product_id": product_id,
                "detection": detection,
                "written": [],
                "message": "No había bloque AEO que retirar.",
            }
        after_body = strip_block(before_body)
        execute("product.template", "write", [int(product_id)], {"website_description": after_body})
        verify = execute(
            "product.template",
            "read",
            [int(product_id)],
            fields=["id", "name", "list_price", "website_description"],
        ) or []
        after = verify[0] if verify else {}
        body = after.get("website_description") or ""
        return {
            "ok": bool(
                after.get("name") == row.get("name")
                and after.get("list_price") == row.get("list_price")
                and "AEO:START v1" not in body
                and "aeo-catalog" not in body
            ),
            "mode": "odoo-xmlrpc",
            "pack": "aeo-rollback",
            "database": database,
            "product_id": product_id,
            "detection": detection,
            "written": ["website_description"],
            "verify": {
                "name_ok": after.get("name") == row.get("name"),
                "price_ok": after.get("list_price") == row.get("list_price"),
                "block_removed": "AEO:START v1" not in body and "aeo-catalog" not in body,
            },
        }
    except xmlrpc_client.Fault as exc:
        return {"ok": False, "mode": "odoo-xmlrpc", "database": database, "message": str(exc)[:240]}
    except Exception as exc:
        return {"ok": False, "mode": "odoo-xmlrpc", "database": database, "message": str(exc)[:240]}
