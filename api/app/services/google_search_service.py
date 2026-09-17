"""Google Search readiness: public checks + OAuth vs Service Account modes."""
from __future__ import annotations

import asyncio
import json
import secrets
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode, urljoin, urlparse

import httpx

from app.config import settings
from app.services.url_analyzer_service import analyze_url

GSC_SCOPES = (
    "https://www.googleapis.com/auth/webmasters.readonly",
    "https://www.googleapis.com/auth/webmasters",
)

_oauth_state: Dict[str, str] = {}
_oauth_tokens: Dict[str, Any] = {}
_session_sa: Dict[str, Any] = {}


def _origin(url: str) -> str:
    parsed = urlparse(url if "://" in url else f"https://{url}")
    if not parsed.scheme or not parsed.netloc:
        return url
    return f"{parsed.scheme}://{parsed.netloc}"


def _sa_payload() -> Optional[Dict[str, Any]]:
    if _session_sa:
        return dict(_session_sa)
    raw = (settings.GOOGLE_SA_JSON or "").strip()
    if not raw and settings.GOOGLE_SA_FILE:
        try:
            with open(settings.GOOGLE_SA_FILE, "r", encoding="utf-8") as fh:
                raw = fh.read()
        except Exception:
            return None
    if not raw:
        return None
    try:
        data = json.loads(raw)
    except Exception:
        return None
    if not isinstance(data, dict):
        return None
    return data


def auth_mode() -> str:
    if settings.google_oauth_configured:
        return "oauth"
    if settings.google_sa_configured or _session_sa:
        return "service_account"
    return "unset"


def oauth_connected() -> bool:
    return bool(_oauth_tokens.get("access_token"))


def status() -> Dict[str, Any]:
    sa = _sa_payload()
    sa_ok = bool(sa and sa.get("type") == "service_account" and sa.get("client_email") and sa.get("private_key"))
    mode = auth_mode()
    if mode == "unset" and sa_ok:
        mode = "service_account"
    return {
        "mode": mode,
        "modes": {
            "oauth": {
                "configured": settings.google_oauth_configured,
                "connected": oauth_connected(),
                "client_id_set": bool(settings.GOOGLE_CLIENT_ID),
                "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            },
            "service_account": {
                "configured": bool(settings.google_sa_configured or sa_ok),
                "valid_json": sa_ok,
                "client_email": (sa or {}).get("client_email") if sa_ok else None,
                "session_override": bool(_session_sa),
            },
        },
        "gsc_site_url": settings.GSC_SITE_URL,
        "frontend_url": settings.FRONTEND_PUBLIC_URL,
        "hint": (
            "OAuth: set GOOGLE_CLIENT_ID + GOOGLE_CLIENT_SECRET, then client consent. "
            "Service Account: set GOOGLE_SA_JSON or GOOGLE_SA_FILE (JSON key) and share the GSC property."
        ),
    }


def set_session_sa(raw_json: str) -> Dict[str, Any]:
    try:
        data = json.loads(raw_json)
    except Exception:
        return {"ok": False, "error": "Invalid JSON"}
    if not isinstance(data, dict) or data.get("type") != "service_account":
        return {"ok": False, "error": "JSON must be a Google service_account key"}
    if not data.get("client_email") or not data.get("private_key"):
        return {"ok": False, "error": "Missing client_email or private_key"}
    _session_sa.clear()
    _session_sa.update(
        {
            "type": data.get("type"),
            "client_email": data.get("client_email"),
            "private_key": data.get("private_key"),
            "project_id": data.get("project_id"),
            "token_uri": data.get("token_uri"),
        }
    )
    return {
        "ok": True,
        "mode": "service_account",
        "client_email": data.get("client_email"),
        "persisted": False,
        "message": "Service account stored in API memory for this session only (not written to disk).",
    }


def start_oauth() -> Dict[str, Any]:
    if not settings.google_oauth_configured:
        return {
            "ok": False,
            "error": "OAuth is not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET on the generator API.",
        }
    state = secrets.token_urlsafe(24)
    _oauth_state["current"] = state
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(GSC_SCOPES),
        "access_type": "offline",
        "prompt": "consent",
        "include_granted_scopes": "true",
        "state": state,
    }
    return {
        "ok": True,
        "auth_url": "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params),
        "state": state,
        "scopes": list(GSC_SCOPES),
    }


async def finish_oauth(code: str, state: str) -> Dict[str, Any]:
    if not code:
        return {"ok": False, "error": "Missing code"}
    expected = _oauth_state.get("current")
    if expected and state and state != expected:
        return {"ok": False, "error": "OAuth state mismatch"}
    if not settings.google_oauth_configured:
        return {"ok": False, "error": "OAuth is not configured"}
    payload = {
        "code": code,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    }
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            r = await client.post("https://oauth2.googleapis.com/token", data=payload)
            data = r.json() if r.content else {}
            if r.status_code >= 400 or not data.get("access_token"):
                return {"ok": False, "error": data.get("error_description") or data.get("error") or r.text[:200]}
            _oauth_tokens.clear()
            _oauth_tokens.update(data)
            return {"ok": True, "token_type": data.get("token_type"), "expires_in": data.get("expires_in")}
    except Exception as exc:
        return {"ok": False, "error": str(exc)[:200]}


async def gsc_sites() -> Dict[str, Any]:
    token = _oauth_tokens.get("access_token")
    if not token:
        return {"ok": False, "error": "No OAuth token. Complete client consent first.", "sites": []}
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            r = await client.get(
                "https://www.googleapis.com/webmasters/v3/sites",
                headers={"Authorization": f"Bearer {token}"},
            )
            data = r.json() if r.content else {}
            if r.status_code >= 400:
                return {"ok": False, "error": data.get("error", {}).get("message") or r.text[:200], "sites": []}
            return {"ok": True, "sites": data.get("siteEntry") or []}
    except Exception as exc:
        return {"ok": False, "error": str(exc)[:200], "sites": []}


def _check(name: str, passed: bool, message: str, detail: Optional[str] = None) -> Dict[str, Any]:
    item = {"name": name, "passed": passed, "message": message}
    if detail:
        item["detail"] = detail
    return item


async def _fetch_text(url: str) -> Dict[str, Any]:
    try:
        async with httpx.AsyncClient(timeout=12.0, follow_redirects=True, headers={"User-Agent": "AEO-generator/1.0"}) as client:
            r = await client.get(url)
            return {"ok": r.status_code < 400, "status_code": r.status_code, "text": r.text or "", "final_url": str(r.url)}
    except Exception as exc:
        return {"ok": False, "status_code": None, "text": "", "error": str(exc)[:200]}


async def readiness(site_url: str, mode: Optional[str] = None) -> Dict[str, Any]:
    site_url = (site_url or settings.GSC_SITE_URL or "").strip()
    if not site_url:
        return {"ok": False, "error": "site_url is required"}
    if "://" not in site_url:
        site_url = "https://" + site_url

    origin = _origin(site_url)
    checks: List[Dict[str, Any]] = []
    page = await asyncio.to_thread(analyze_url, site_url)
    page_ok = bool(page.status_code and page.status_code < 400 and not page.error)
    checks.append(
        _check(
            "Live URL fetch",
            page_ok,
            f"HTTP {page.status_code}" if page.status_code else (page.error or "Fetch failed"),
            page.title,
        )
    )
    checks.append(_check("Title tag", bool(page.title), page.title or "No <title> found"))
    checks.append(
        _check(
            "Meta description",
            bool(page.meta_description),
            (page.meta_description[:160] + "…") if page.meta_description and len(page.meta_description) > 160 else (page.meta_description or "Missing meta description"),
        )
    )
    checks.append(_check("H1 present", bool(page.h1_list), f"{len(page.h1_list or [])} H1 tag(s)"))

    robots = await _fetch_text(urljoin(origin + "/", "robots.txt"))
    robots_ok = bool(robots.get("ok") and "user-agent" in (robots.get("text") or "").lower())
    checks.append(
        _check(
            "robots.txt",
            robots_ok,
            f"HTTP {robots.get('status_code')}" if robots.get("status_code") else robots.get("error") or "Not found",
        )
    )
    sitemap = await _fetch_text(urljoin(origin + "/", "sitemap.xml"))
    sitemap_text = sitemap.get("text") or ""
    sitemap_ok = bool(sitemap.get("ok") and ("<urlset" in sitemap_text.lower() or "<sitemapindex" in sitemap_text.lower()))
    checks.append(
        _check(
            "sitemap.xml",
            sitemap_ok,
            f"HTTP {sitemap.get('status_code')}" if sitemap.get("status_code") else sitemap.get("error") or "Not found",
        )
    )

    auth = status()
    chosen = (mode or auth["mode"] or "unset").lower()
    if chosen not in ("oauth", "service_account", "unset"):
        chosen = auth["mode"]

    if chosen == "oauth":
        checks.append(
            _check(
                "OAuth client configured",
                auth["modes"]["oauth"]["configured"],
                "GOOGLE_CLIENT_ID / SECRET set" if auth["modes"]["oauth"]["configured"] else "Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET",
            )
        )
        checks.append(
            _check(
                "Client consent",
                auth["modes"]["oauth"]["connected"],
                "Access token present" if auth["modes"]["oauth"]["connected"] else "User must grant Search Console access",
            )
        )
        sites = []
        if auth["modes"]["oauth"]["connected"]:
            listed = await gsc_sites()
            sites = listed.get("sites") or []
            matched = any(site_url.rstrip("/") in (s.get("siteUrl") or "") or (s.get("siteUrl") or "").rstrip("/") in site_url for s in sites)
            checks.append(_check("GSC property visible", matched or bool(sites), f"{len(sites)} property(ies) on this account"))
    elif chosen == "service_account":
        sa_ok = auth["modes"]["service_account"]["valid_json"] or auth["modes"]["service_account"]["configured"]
        checks.append(
            _check(
                "Service account key",
                bool(sa_ok),
                auth["modes"]["service_account"].get("client_email") or "Paste or set GOOGLE_SA_JSON",
            )
        )
        checks.append(
            _check(
                "GSC property share",
                False,
                "Share the Search Console property with the SA client_email (Users and permissions).",
            )
        )
    else:
        checks.append(
            _check(
                "Auth mode selected",
                False,
                "Choose OAuth (client consent) or Service Account. Public crawl checks still run.",
            )
        )

    passed = sum(1 for c in checks if c["passed"])
    ready = passed >= 4 and page_ok
    return {
        "ok": True,
        "ready": ready,
        "site_url": site_url,
        "origin": origin,
        "mode": chosen,
        "auth": auth,
        "passed": passed,
        "total": len(checks),
        "checks": checks,
        "page": {
            "title": page.title,
            "meta_description": page.meta_description,
            "h1_list": page.h1_list,
            "word_count": page.word_count,
            "status_code": page.status_code,
        },
        "next": (
            "Continue to AEO pack generation."
            if ready
            else "Fix failed checks or continue anyway after reviewing the list."
        ),
    }
