"""HTTP client for AEO Core (`server.py` on :18642). Never replaces Core."""
from __future__ import annotations

from typing import Any, Dict, List, Tuple

import httpx

from app.config import settings

PLATFORMS = ("odoo", "prestashop", "woocommerce")

WRITE_TEMPLATES = (
    "/api/connectors/{platform}/write-seo",
    "/api/connectors/{platform}/write_seo",
    "/api/{platform}/write-seo",
    "/api/{platform}/write_seo",
    "/connectors/{platform}/write-seo",
    "/{platform}/write-seo",
    "/write-seo",
    "/api/write-seo",
)

VERIFY_TEMPLATES = (
    "/api/connectors/{platform}/verify",
    "/api/{platform}/verify",
    "/connectors/{platform}/verify",
    "/{platform}/verify",
    "/verify",
    "/api/verify",
)

HEALTH_PATHS = ("/health", "/api/health", "/", "/openapi.json")


def core_base() -> str:
    return (settings.CORE_BASE_URL or "http://172.17.0.1:18642").rstrip("/")


def _timeout() -> httpx.Timeout:
    sec = float(getattr(settings, "CORE_TIMEOUT_SEC", 25.0))
    return httpx.Timeout(sec, connect=4.0)


async def probe_core() -> Dict[str, Any]:
    base = core_base()
    tried: List[Dict[str, Any]] = []
    reachable = False
    openapi_paths: List[str] = []
    async with httpx.AsyncClient(timeout=_timeout(), follow_redirects=True) as client:
        for path in HEALTH_PATHS:
            url = f"{base}{path}"
            entry: Dict[str, Any] = {"url": url, "ok": False}
            try:
                r = await client.get(url)
                entry["status_code"] = r.status_code
                entry["ok"] = r.status_code < 500
                snippet = (r.text or "")[:240]
                entry["body_preview"] = snippet
                if r.status_code < 500:
                    reachable = True
                if path == "/openapi.json" and r.status_code == 200:
                    try:
                        data = r.json()
                        openapi_paths = sorted((data.get("paths") or {}).keys())
                    except Exception:
                        pass
            except Exception as exc:
                entry["error"] = str(exc)[:200]
            tried.append(entry)
    return {
        "reachable": reachable,
        "core_url": base,
        "message": (
            "AEO Core is reachable."
            if reachable
            else "AEO Core :18642 is not reachable. Start Core (server.py); this generator does not replace it."
        ),
        "probes": tried,
        "openapi_paths": openapi_paths,
        "platforms": list(PLATFORMS),
    }


def _expand(templates: Tuple[str, ...], platform: str) -> List[str]:
    return [t.format(platform=platform) for t in templates]


async def _post_first_hit(
    paths: List[str],
    payload: Dict[str, Any],
) -> Dict[str, Any]:
    base = core_base()
    attempts: List[Dict[str, Any]] = []
    async with httpx.AsyncClient(timeout=_timeout(), follow_redirects=True) as client:
        for path in paths:
            url = f"{base}{path}"
            attempt: Dict[str, Any] = {"url": url}
            try:
                r = await client.post(url, json=payload)
                attempt["status_code"] = r.status_code
                try:
                    body: Any = r.json()
                except Exception:
                    body = {"raw": (r.text or "")[:800]}
                attempt["body"] = body
                # 404 = wrong path; keep looking. Anything else is Core answering.
                if r.status_code != 404:
                    attempt["hit"] = True
                    return {
                        "ok": 200 <= r.status_code < 300,
                        "forwarded": True,
                        "core_url": base,
                        "path": path,
                        "status_code": r.status_code,
                        "data": body,
                        "attempts": attempts + [attempt],
                    }
                attempt["hit"] = False
            except Exception as exc:
                attempt["error"] = str(exc)[:200]
                attempt["hit"] = False
            attempts.append(attempt)
    return {
        "ok": False,
        "forwarded": False,
        "core_url": base,
        "status_code": None,
        "data": None,
        "message": (
            "No matching Core write/verify route answered (not 404). "
            "Confirm Core is running on :18642; generator only proxies."
        ),
        "attempts": attempts,
    }


async def write_seo(platform: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    platform = (platform or "").strip().lower()
    if platform not in PLATFORMS:
        return {"ok": False, "error": f"Unsupported platform '{platform}'", "platforms": list(PLATFORMS)}
    body = {**payload, "platform": platform}
    result = await _post_first_hit(_expand(WRITE_TEMPLATES, platform), body)
    result["action"] = "write-seo"
    result["platform"] = platform
    return result


async def verify_seo(platform: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    platform = (platform or "").strip().lower()
    if platform not in PLATFORMS:
        return {"ok": False, "error": f"Unsupported platform '{platform}'", "platforms": list(PLATFORMS)}
    body = {**payload, "platform": platform}
    result = await _post_first_hit(_expand(VERIFY_TEMPLATES, platform), body)
    result["action"] = "verify"
    result["platform"] = platform
    return result
