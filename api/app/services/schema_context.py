"""Public schema snapshot + hostname graph for General Pack prompts."""
from __future__ import annotations

import json
import re
from typing import Any, Dict, List
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from app.services.site_guard import keep_https, normalize_host


def _abs(base: str, href: str) -> str:
    try:
        return urljoin(base, href)
    except Exception:
        return href


def _same_host(base: str, other: str) -> bool:
    return normalize_host(base) == normalize_host(other)


async def snapshot(site_url: str) -> Dict[str, Any]:
    url = keep_https(site_url)
    host = normalize_host(url)
    out: Dict[str, Any] = {
        "url": url,
        "host": host,
        "title": None,
        "h1": None,
        "meta_description": None,
        "canonical": None,
        "json_ld": [],
        "internal_links": [],
        "ok": False,
    }
    if not url:
        return out
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(18.0, connect=6.0), follow_redirects=True) as client:
            r = await client.get(url, headers={"User-Agent": "Arkiphere-Optimizator/1.0"})
            html = r.text or ""
            out["status_code"] = r.status_code
            out["final_url"] = str(r.url)
            out["ok"] = r.status_code < 400 and bool(html)
    except Exception as exc:
        out["error"] = str(exc)[:200]
        return out
    soup = BeautifulSoup(html, "html.parser")
    title = soup.find("title")
    out["title"] = (title.get_text(" ", strip=True) if title else "")[:180] or None
    h1 = soup.find("h1")
    out["h1"] = (h1.get_text(" ", strip=True) if h1 else "")[:180] or None
    desc = soup.find("meta", attrs={"name": re.compile(r"^description$", re.I)})
    if desc and desc.get("content"):
        out["meta_description"] = str(desc.get("content"))[:240]
    canonical = soup.find("link", attrs={"rel": re.compile(r"canonical", re.I)})
    if canonical and canonical.get("href"):
        out["canonical"] = _abs(url, str(canonical.get("href")))
    for script in soup.find_all("script", attrs={"type": re.compile(r"ld\+json", re.I)}):
        raw = (script.string or script.get_text() or "").strip()
        if not raw:
            continue
        try:
            parsed = json.loads(raw)
            out["json_ld"].append(parsed)
        except Exception:
            out["json_ld"].append({"raw": raw[:400]})
        if len(out["json_ld"]) >= 4:
            break
    links: List[str] = []
    seen = set()
    for a in soup.find_all("a", href=True):
        href = _abs(url, a["href"])
        if not href.startswith("http"):
            continue
        if not _same_host(url, href):
            continue
        parsed = urlparse(href)
        clean = f"{parsed.scheme}://{parsed.netloc}{parsed.path or '/'}"
        if clean in seen:
            continue
        seen.add(clean)
        links.append(clean)
        if len(links) >= 12:
            break
    out["internal_links"] = links
    types = []
    for block in out["json_ld"]:
        if isinstance(block, dict):
            kind = block.get("@type") or block.get("type")
            if kind:
                types.append(kind if isinstance(kind, str) else str(kind))
        elif isinstance(block, list):
            for item in block:
                if isinstance(item, dict) and item.get("@type"):
                    types.append(str(item.get("@type")))
    out["schema_types"] = types[:8]
    return out


def prompt_facts(snapshot_data: Dict[str, Any], extra: str = "") -> str:
    parts = [
        f"Hostname: {snapshot_data.get('host') or ''}",
        f"Live URL: {snapshot_data.get('final_url') or snapshot_data.get('url') or ''}",
        f"Page title: {snapshot_data.get('title') or '(none)'}",
        f"H1: {snapshot_data.get('h1') or '(none)'}",
        f"Meta: {snapshot_data.get('meta_description') or '(none)'}",
        f"Schema types: {', '.join(snapshot_data.get('schema_types') or []) or '(none)'}",
        f"Internal graph: {', '.join((snapshot_data.get('internal_links') or [])[:8]) or '(none)'}",
    ]
    ld = snapshot_data.get("json_ld") or []
    if ld:
        parts.append("JSON-LD snapshot: " + json.dumps(ld[:2], ensure_ascii=False)[:900])
    if extra:
        parts.append(f"Business facts: {extra}")
    return "\n".join(parts)
