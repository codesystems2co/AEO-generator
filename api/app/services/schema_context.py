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
        async with httpx.AsyncClient(timeout=httpx.Timeout(6.0, connect=3.0), follow_redirects=True) as client:
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


def customer_reading(snapshot_data: Dict[str, Any], locale: str = "es") -> str:
    """Plain sentence for the wizard. Empty crawl fields are not printed as labels."""
    host = (snapshot_data.get("host") or snapshot_data.get("url") or "the shop").strip()
    title = (snapshot_data.get("title") or "").strip()
    h1 = (snapshot_data.get("h1") or "").strip()
    meta = (snapshot_data.get("meta_description") or "").strip()
    types = [str(item).strip() for item in (snapshot_data.get("schema_types") or []) if str(item).strip()]
    links = [str(item).strip() for item in (snapshot_data.get("internal_links") or []) if str(item).strip()]
    spanish = (locale or "es").lower().startswith("es")
    if not title and not h1 and not meta:
        if spanish:
            text = f"La tienda {host} responde, pero la página todavía no tiene título, encabezado ni descripción."
        else:
            text = f"The shop {host} is online, but the page still has no title, heading, or description."
    else:
        bits = []
        if spanish:
            if title:
                bits.append(f"El título es «{title}».")
            if h1:
                bits.append(f"El encabezado es «{h1}».")
            if meta:
                bits.append(meta if meta.endswith(".") else f"{meta}.")
        else:
            if title:
                bits.append(f"The title is “{title}”.")
            if h1:
                bits.append(f"The heading is “{h1}”.")
            if meta:
                bits.append(meta if meta.endswith(".") else f"{meta}.")
        text = " ".join(bits)
    if spanish:
        if types:
            text += " Hay datos estructurados: " + ", ".join(types) + "."
        else:
            text += " No hay datos estructurados."
        if links:
            text += f" Se leyeron {len(links)} enlaces internos."
    else:
        if types:
            text += " Structured data: " + ", ".join(types) + "."
        else:
            text += " There is no structured data."
        if links:
            text += f" {len(links)} internal links were read."
    return text.strip()


def prompt_facts(snapshot_data: Dict[str, Any], extra: str = "") -> str:
    """Human reading of the crawl. Extra business notes are appended as a sentence."""
    reading = customer_reading(snapshot_data, "es")
    note = (extra or "").strip()
    if note and "Page title:" not in note and "Internal graph:" not in note:
        reading = f"{reading} {note}".strip()
    return reading
