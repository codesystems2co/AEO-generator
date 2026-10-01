"""Bind pack/wizard/google calls to the license consume source of truth."""
from __future__ import annotations

from typing import Any, Dict, Optional
from urllib.parse import urlparse

from fastapi import HTTPException

from app.services.entitlement_service import consume
from app.services.i18n_copy import t


def keep_https(value: Optional[str]) -> str:
    raw = (value or "").strip()
    if not raw:
        return ""
    if raw.lower().startswith("https://"):
        return raw
    if raw.lower().startswith("http://"):
        return raw
    return f"https://{raw.lstrip('/')}"


def normalize_shop_url(value: Optional[str]) -> str:
    """Platform RPC URL; keep http for local gateway (.local, localhost)."""
    raw = (value or "").strip()
    if not raw:
        return ""
    lower = raw.lower()
    if lower.startswith("http://") or lower.startswith("https://"):
        return raw.rstrip("/")
    return f"http://{raw.lstrip('/')}".rstrip("/")


def normalize_host(value: Optional[str]) -> str:
    url = keep_https(value)
    if not url:
        return ""
    try:
        host = (urlparse(url).hostname or "").strip().lower()
    except Exception:
        return ""
    if host.startswith("www."):
        host = host[4:]
    return host


def is_gateway_shop_host(value: Optional[str]) -> bool:
    host = normalize_host(normalize_shop_url(value))
    if not host:
        return False
    return (
        host.endswith(".aeo.local")
        or host == "localhost"
        or host.startswith("127.")
        or host.startswith("10.")
        or host.startswith("192.168.")
    )


def hosts_match(left: Optional[str], right: Optional[str]) -> bool:
    a = normalize_host(left)
    b = normalize_host(right)
    return bool(a and b and a == b)


def resolve_register_shop_url(
    order_line_shop: Optional[str],
    body_shop_url: Optional[str] = None,
    body_url: Optional[str] = None,
) -> str:
    """
    One shop hostname per order line (Arkiphere SoT).
    When the line has a URL, the wizard must not override it.
    """
    line_url = normalize_shop_url(order_line_shop)
    typed = normalize_shop_url(body_shop_url) or normalize_shop_url(body_url)
    if line_url:
        if typed and normalize_host(typed) and normalize_host(typed) != normalize_host(line_url):
            raise HTTPException(
                status_code=400,
                detail=(
                    "La URL de la tienda viene de la línea del pedido en Arkiphere. "
                    "Solo hay un hostname por pedido; no se puede cambiar desde el asistente."
                ),
            )
        return line_url
    if typed:
        return typed
    raise HTTPException(
        status_code=400,
        detail=(
            "El pedido no tiene URL de tienda en la línea Optimizator. "
            "Configúrela en Arkiphere (pedido / línea) antes de conectar."
        ),
    )


def extract_license(
    header: Optional[str] = None,
    body_license: Optional[str] = None,
    body_key: Optional[str] = None,
) -> str:
    return (header or body_license or body_key or "").strip()


def bind_license_site(
    license_key: Optional[str],
    requested_site: Optional[str] = None,
    github_login: Optional[str] = None,
) -> Dict[str, Any]:
    key = (license_key or "").strip()
    if not key:
        raise HTTPException(
            status_code=403,
            detail="Falta la clave de activación. El generador no acepta un sitio sin pedido.",
        )
    data = consume(key, github_login=github_login, site=None)
    order_site = keep_https(data.get("aeo_site_url"))
    if data.get("allowed") is not True:
        raise HTTPException(
            status_code=403,
            detail=data.get("message")
            or t("es", "entitlement.noOrder"),
        )
    if not order_site:
        raise HTTPException(
            status_code=403,
            detail="El pedido no tiene un sitio confirmado. Abre AEO desde Arkiphere.",
        )
    bound = dict(data)
    bound["bound_site_url"] = order_site
    bound["bound_host"] = normalize_host(order_site)
    return bound
