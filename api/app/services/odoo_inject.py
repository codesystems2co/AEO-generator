"""Direct Odoo website SEO write when Core is down and the customer typed RPC details."""
from __future__ import annotations

from typing import Any, Dict, Optional
from urllib.parse import urlparse
from xmlrpc import client as xmlrpc_client


def _auth(url: str, database: str, username: str, api_key: str):
    base = (url or "").rstrip("/")
    common = xmlrpc_client.ServerProxy(f"{base}/xmlrpc/2/common", allow_none=True)
    uid = common.authenticate(database, username, api_key, {})
    if not uid:
        raise RuntimeError("Odoo authentication failed")
    models = xmlrpc_client.ServerProxy(f"{base}/xmlrpc/2/object", allow_none=True)
    return uid, models


def inject_website_seo(connection: Dict[str, Any], seo: Dict[str, Any], target: Optional[str] = None) -> Dict[str, Any]:
    url = (connection.get("url") or "").strip()
    database = (connection.get("database") or "").strip()
    username = (connection.get("username") or "").strip()
    api_key = (connection.get("api_key") or "").strip()
    if not (url and database and username and api_key):
        return {"ok": False, "mode": "odoo-xmlrpc", "message": "Faltan URL, base, usuario o clave API de Odoo."}
    title = (seo.get("title") or "").strip()
    meta = (seo.get("meta_description") or "").strip()
    keywords = seo.get("keywords") or []
    if isinstance(keywords, list):
        kw = ", ".join(str(k) for k in keywords if k)
    else:
        kw = str(keywords or "")
    try:
        uid, models = _auth(url, database, username, api_key)
    except Exception as exc:
        return {"ok": False, "mode": "odoo-xmlrpc", "message": str(exc)[:240]}

    def execute(model: str, method: str, *args, **kwargs):
        return models.execute_kw(database, uid, api_key, model, method, list(args), kwargs or {})

    path = "/"
    if target and target.startswith("/"):
        path = target
    elif target:
        try:
            parsed = urlparse(target if "://" in target else f"https://x{target}")
            path = parsed.path or "/"
        except Exception:
            path = "/"
    try:
        pages = execute(
            "website.page",
            "search_read",
            ["|", ("url", "=", path), ("url", "=", path.rstrip("/") or "/")],
            fields=["id", "url", "name", "website_meta_title", "website_meta_description", "is_published"],
            limit=5,
        ) or []
        if not pages:
            pages = execute(
                "website.page",
                "search_read",
                [("is_published", "=", True)],
                fields=["id", "url", "name", "website_meta_title", "website_meta_description", "is_published"],
                limit=5,
                order="id",
            ) or []
        if not pages:
            return {"ok": False, "mode": "odoo-xmlrpc", "message": "No hay website.page publicable."}
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
        return {"ok": False, "mode": "odoo-xmlrpc", "message": str(exc)[:240]}
    except Exception as exc:
        return {"ok": False, "mode": "odoo-xmlrpc", "message": str(exc)[:240]}
