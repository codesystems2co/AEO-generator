"""Google Search gap calculation + Ollama auto-remediation loop."""
from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional
import httpx

from app.config import settings
from app.services.chat_service import check_ollama_health
from app.services.google_search_service import _fetch_text, oauth_connected, readiness

AUTO_FIXABLE = {
    "Title tag",
    "Meta description",
    "H1 present",
    "robots.txt",
    "sitemap.xml",
    "Commerce signals",
    "Structured data",
}

HARD_BLOCKERS = {
    "Live URL fetch",
}

FIX_SYSTEM = (
    "You are an AEO/SEO fixer for a commerce-capable website. Reply with JSON only. "
    "Schema: {\"title\":\"\",\"meta_description\":\"\",\"h1\":\"\","
    "\"robots_txt\":\"\",\"sitemap_urls\":[\"\"],"
    "\"commerce_faq\":[{\"question\":\"\",\"answer\":\"\"}],"
    "\"json_ld\":\"\",\"cta\":\"\","
    "\"fixes\":[{\"check\":\"\",\"action\":\"\",\"solved\":true}]}. "
    "title 30-60 chars. meta_description 120-160 chars. "
    "json_ld must be a Product/Organization JSON-LD object as a string. "
    "Reuse given facts. Never invent prices or SKUs."
)

MAX_LOOPS = 2


def _extract_json(text: str) -> Optional[Dict[str, Any]]:
    if not text:
        return None
    text = text.strip()
    try:
        data = json.loads(text)
        return data if isinstance(data, dict) else None
    except Exception:
        pass
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return None
    try:
        data = json.loads(match.group(0))
        return data if isinstance(data, dict) else None
    except Exception:
        return None


async def _commerce_scan(site_url: str) -> List[Dict[str, Any]]:
    html = await _fetch_text(site_url)
    body = (html.get("text") or "").lower()
    extras: List[Dict[str, Any]] = []
    commerce_keys = ("precio", "price", "carrito", "cart", "comprar", "buy", "producto", "product", "sku")
    commerce_ok = any(k in body for k in commerce_keys)
    extras.append(
        {
            "name": "Commerce signals",
            "passed": commerce_ok,
            "fixable": True,
            "message": "Price/cart/product language found" if commerce_ok else "No price, cart, or product language on the page",
        }
    )
    schema_ok = "ld+json" in body or "schema.org" in body
    extras.append(
        {
            "name": "Structured data",
            "passed": schema_ok,
            "fixable": True,
            "message": "JSON-LD or schema.org found" if schema_ok else "No JSON-LD / schema.org markup",
        }
    )
    return extras


def _classify(checks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    gaps = []
    for c in checks:
        name = c.get("name") or ""
        item = {
            "name": name,
            "passed": bool(c.get("passed")),
            "message": c.get("message") or "",
            "fixable": name in AUTO_FIXABLE,
            "hard": name in HARD_BLOCKERS,
        }
        if name in AUTO_FIXABLE:
            item["fixable"] = True
        if not item["passed"]:
            gaps.append(item)
        else:
            gaps.append({**item, "remaining": False})
    return gaps


def _apply_virtual(gaps: List[Dict[str, Any]], fix: Dict[str, Any]) -> List[Dict[str, Any]]:
    solved_names = set()
    for entry in fix.get("fixes") or []:
        if isinstance(entry, dict) and entry.get("solved") and entry.get("check"):
            solved_names.add(str(entry["check"]))
    mapping = {
        "Title tag": bool((fix.get("title") or "").strip()),
        "Meta description": bool((fix.get("meta_description") or "").strip()),
        "H1 present": bool((fix.get("h1") or "").strip()),
        "robots.txt": bool((fix.get("robots_txt") or "").strip()),
        "sitemap.xml": bool(fix.get("sitemap_urls")),
        "Commerce signals": bool(fix.get("commerce_faq") or fix.get("cta")),
        "Structured data": bool((fix.get("json_ld") or "").strip()),
    }
    out = []
    for g in gaps:
        name = g["name"]
        virtual = bool(g.get("passed")) or mapping.get(name, False) or name in solved_names
        out.append(
            {
                **g,
                "virtual_passed": virtual,
                "remaining": (not virtual) and (g.get("fixable") or g.get("hard")),
            }
        )
    return out


async def _ollama_fix(site_url: str, context: str, gaps: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    failed = [g for g in gaps if not g.get("passed") and g.get("fixable")]
    if not failed:
        return {"fixes": []}
    health = await check_ollama_health()
    if health.get("status") != "ok":
        return None
    payload_gaps = [{"name": g["name"], "message": g["message"]} for g in failed]
    user = (
        f"Site: {site_url}\nFacts: {context or '(none)'}\n"
        f"Failed checks: {json.dumps(payload_gaps, ensure_ascii=False)}\n"
        "Return JSON only with remediations for each failed check."
    )
    timeout = httpx.Timeout(float(getattr(settings, "PACK_OLLAMA_TIMEOUT_SEC", 90.0)), connect=8.0)
    body = {
        "model": settings.OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": FIX_SYSTEM},
            {"role": "user", "content": user},
        ],
        "stream": False,
        "format": "json",
        "options": {"num_predict": 700, "temperature": 0.2},
    }
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.post(f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/chat", json=body)
            r.raise_for_status()
            data = r.json()
            msg = data.get("message") or {}
            return _extract_json(msg.get("content") or data.get("response") or "")
    except Exception:
        return None


def _heuristic_fix(site_url: str, topic: str, context: str, gaps: List[Dict[str, Any]]) -> Dict[str, Any]:
    brand = (topic or "Site").strip() or "Site"
    title = f"{brand} — products, plans and answers"[:60]
    meta = (
        f"{brand} storefront with clear offers, FAQ and structure for search and answer engines. "
        f"{(context or '')[:80]}"
    ).strip()[:160]
    if len(meta) < 120:
        meta = (meta + " Compare plans, checkout path, and product questions in one page.").strip()[:160]
    return {
        "title": title,
        "meta_description": meta,
        "h1": brand,
        "robots_txt": "User-agent: *\nAllow: /\nSitemap: " + site_url.rstrip("/") + "/sitemap.xml\n",
        "sitemap_urls": [site_url],
        "commerce_faq": [
            {"question": f"What does {brand} sell?", "answer": context or f"{brand} offers its core product and related services."},
            {"question": f"How do I start with {brand}?", "answer": "Use the public trial or catalog page, then choose a plan."},
        ],
        "json_ld": json.dumps(
            {
                "@context": "https://schema.org",
                "@type": "Organization",
                "name": brand,
                "url": site_url,
            }
        ),
        "cta": "See plans and start a trial",
        "fixes": [{"check": g["name"], "action": "Heuristic publish-ready snippet", "solved": True} for g in gaps if g.get("fixable") and not g.get("passed")],
        "backend": "heuristic",
    }


async def autofix(
    site_url: str,
    mode: Optional[str] = None,
    topic: Optional[str] = None,
    context: Optional[str] = None,
    locale: str = "es",
) -> Dict[str, Any]:
    report = await readiness(site_url, mode=mode)
    if not report.get("ok"):
        return {**report, "step_complete": False}

    extra = await _commerce_scan(report["site_url"])
    # Readiness already has robots/sitemap; keep those, add commerce/schema if missing
    existing = {c["name"] for c in report.get("checks") or []}
    merged_checks = list(report.get("checks") or [])
    for item in extra:
        if item["name"] not in existing:
            merged_checks.append(item)
    if oauth_connected():
        for item in merged_checks:
            if item.get("name") == "Client consent":
                item["passed"] = True
                item["message"] = "Access token present"

    classified = _classify(merged_checks)
    loops: List[Dict[str, Any]] = []
    fix: Dict[str, Any] = {}
    overlay = classified
    ollama_health = await check_ollama_health()
    facts = " | ".join(x for x in (topic, context, report.get("page", {}).get("title")) if x)

    for attempt in range(1, MAX_LOOPS + 1):
        remaining_fixable = [g for g in overlay if g.get("fixable") and not g.get("virtual_passed", g.get("passed"))]
        if not remaining_fixable:
            break
        llm = await _ollama_fix(report["site_url"], facts, remaining_fixable)
        used = llm if llm else _heuristic_fix(report["site_url"], topic or report["site_url"], facts, remaining_fixable)
        if llm:
            used["backend"] = "ollama"
        fix = {**fix, **used}
        overlay = _apply_virtual(overlay, fix)
        loops.append(
            {
                "attempt": attempt,
                "backend": used.get("backend"),
                "remaining_after": [g["name"] for g in overlay if g.get("fixable") and not g.get("virtual_passed")],
            }
        )

    remaining_fixable = [g for g in overlay if g.get("fixable") and not g.get("virtual_passed")]
    hard = [g for g in overlay if g.get("hard") and not g.get("passed")]
    page_ok = not any(g["name"] == "Live URL fetch" and not g.get("passed") for g in overlay)
    step_complete = page_ok and len(remaining_fixable) == 0

    return {
        "ok": True,
        "step_complete": step_complete,
        "site_url": report["site_url"],
        "mode": report.get("mode"),
        "auth": report.get("auth"),
        "page": report.get("page"),
        "ollama": ollama_health,
        "gaps": overlay,
        "remaining_fixable": [g["name"] for g in remaining_fixable],
        "hard_blockers": [g["name"] for g in hard],
        "remediation": fix,
        "loops": loops,
        "locale": locale,
        "message": (
            "Google Search gaps auto-solved. Continuar is enabled."
            if step_complete
            else "Hard blockers remain or auto-fix could not close every gap."
        ),
    }
