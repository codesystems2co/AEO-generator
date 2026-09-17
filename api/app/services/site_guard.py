"""Bind pack/wizard/google calls to the license consume source of truth."""
from __future__ import annotations

from typing import Any, Dict, Optional
from urllib.parse import urlparse

from fastapi import HTTPException

from app.services.entitlement_service import consume


def keep_https(value: Optional[str]) -> str:
    raw = (value or "").strip()
    if not raw:
        return ""
    if raw.lower().startswith("https://"):
        return raw
    if raw.lower().startswith("http://"):
        return f"https://{raw[7:]}"
    return f"https://{raw.lstrip('/')}"


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


def hosts_match(left: Optional[str], right: Optional[str]) -> bool:
    a = normalize_host(left)
    b = normalize_host(right)
    return bool(a and b and a == b)


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
    requested = keep_https(requested_site) if requested_site else ""
    data = consume(key, github_login=github_login, site=requested or None)
    order_site = keep_https(data.get("aeo_site_url"))
    if requested and order_site and not hosts_match(requested, order_site):
        raise HTTPException(
            status_code=403,
            detail=(
                "El sitio no coincide con el pedido confirmado. "
                f"Usa {normalize_host(order_site) or 'el hostname del pedido'}."
            ),
        )
    if requested and not order_site and data.get("allowed") is not True:
        raise HTTPException(
            status_code=403,
            detail="El sitio no coincide con el pedido confirmado.",
        )
    if data.get("allowed") is not True:
        raise HTTPException(
            status_code=403,
            detail=data.get("message")
            or "No hay un pedido confirmado de Search Engine Optimizator.",
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
