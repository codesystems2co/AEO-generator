"""Ollama-backed AEO + SEO pack with a human-readable tree resume."""
from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

import httpx

from app.config import settings
from app.schemas import AEORequest, KeywordsRequest, MetaTagsRequest, SEOScoreRequest
from app.services.aeo_service import generate_aeo_suggestions
from app.services.chat_service import check_ollama_health
from app.services.keywords_service import extract_keywords
from app.services.meta_service import generate_meta_tags
from app.services.seo_score_service import calculate_seo_score

PACK_SYSTEM = (
    "You generate publish-ready AEO and SEO packs. Reply with JSON only, no markdown. "
    "Schema: {\"title\":\"\",\"meta_description\":\"\",\"summary\":\"\","
    "\"keywords\":[\"\"],\"h2\":[\"\"],\"faq\":[{\"question\":\"\",\"answer\":\"\"}],"
    "\"entities\":[\"\"],\"tips\":[\"\"]}. "
    "title 30-60 chars. meta_description 120-160 chars. "
    "8 keywords, 5 h2, 4 faq with full answers. Reuse given facts. Never invent products."
)


def _tree_node(label: str, value: Optional[str] = None, children: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    node: Dict[str, Any] = {"label": label}
    if value:
        node["value"] = value
    if children:
        node["children"] = children
    return node


def _resume_lines(nodes: List[Dict[str, Any]], prefix: str = "") -> List[str]:
    lines: List[str] = []
    for i, node in enumerate(nodes):
        last = i == len(nodes) - 1
        branch = "└── " if last else "├── "
        child_prefix = prefix + ("    " if last else "│   ")
        label = node.get("label") or ""
        value = node.get("value")
        extra = f" — {value}" if value else ""
        lines.append(f"{prefix}{branch}{label}{extra}")
        kids = node.get("children") or []
        if kids:
            lines.extend(_resume_lines(kids, child_prefix))
    return lines


def build_tree(topic: str, aeo: Dict[str, Any], seo: Dict[str, Any]) -> List[Dict[str, Any]]:
    faqs = aeo.get("questions_answers") or []
    h2s = aeo.get("structured_sections") or []
    entities = aeo.get("key_entities") or []
    keywords = seo.get("keywords") or []
    score = seo.get("score") or {}
    return [
        _tree_node(
            "AEO",
            children=[
                _tree_node("Title", aeo.get("suggested_title")),
                _tree_node("Summary", (aeo.get("summary") or "")[:180]),
                _tree_node("Entities", ", ".join(entities[:8]) if entities else "—"),
                _tree_node(
                    f"FAQ ({len(faqs)})",
                    children=[_tree_node(qa.get("question") or f"Q{i+1}", qa.get("answer")) for i, qa in enumerate(faqs)],
                ),
                _tree_node(
                    f"H2 ({len(h2s)})",
                    children=[_tree_node(h) for h in h2s],
                ),
            ],
        ),
        _tree_node(
            "SEO",
            children=[
                _tree_node("Title tag", seo.get("title")),
                _tree_node("Meta description", seo.get("meta_description")),
                _tree_node("Keywords", ", ".join(keywords[:10]) if keywords else "—"),
                _tree_node("Canonical", seo.get("canonical") or "—"),
                _tree_node(
                    "Score",
                    f"{score.get('overall_score', '—')} / {score.get('max_score', '—')} ({score.get('grade', '—')})",
                ),
            ],
        ),
    ]


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


async def _ollama_pack(topic: str, context: str, locale: str) -> Optional[Dict[str, Any]]:
    base = settings.OLLAMA_BASE_URL.rstrip("/")
    model = settings.OLLAMA_MODEL
    timeout = httpx.Timeout(float(getattr(settings, "PACK_OLLAMA_TIMEOUT_SEC", 90.0)), connect=8.0)
    user = (
        f"Locale: {locale}\nTopic: {topic}\nFacts:\n{context or '(none)'}\n"
        "Return JSON only."
    )
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": PACK_SYSTEM},
            {"role": "user", "content": user},
        ],
        "stream": False,
        "format": "json",
        "options": {"num_predict": 700, "temperature": 0.3},
    }
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.post(f"{base}/api/chat", json=payload)
            r.raise_for_status()
            data = r.json()
            msg = data.get("message") or {}
            return _extract_json(msg.get("content") or data.get("response") or "")
    except Exception:
        return None


def _heuristic_pack(topic: str, context: Optional[str], url: Optional[str]) -> Dict[str, Any]:
    aeo = generate_aeo_suggestions(
        AEORequest(topic=topic, context=context or url, include_qa=True, include_entities=True)
    ).model_dump()
    title = (aeo.get("suggested_title") or topic)[:60]
    summary = aeo.get("summary") or f"Guide to {topic}."
    meta_desc = summary[:160]
    if len(meta_desc) < 120:
        meta_desc = (meta_desc + " Optimized for search and answer engines. Clear facts, FAQ, and structure.").strip()[:160]
    source_text = " ".join(
        [
            title,
            summary,
            " ".join(aeo.get("key_entities") or []),
            " ".join(aeo.get("structured_sections") or []),
            " ".join(f"{qa.get('question')} {qa.get('answer')}" for qa in (aeo.get("questions_answers") or [])),
            context or "",
        ]
    )
    if len(source_text) < 10:
        source_text = f"{topic} answer engine optimization search engine optimization keywords FAQ headings."
    kws = extract_keywords(KeywordsRequest(text=source_text, max_keywords=8))
    keywords = [k.keyword for k in kws.keywords]
    content_parts = [summary]
    content_parts.extend(f"## {h}" for h in (aeo.get("structured_sections") or []))
    for qa in aeo.get("questions_answers") or []:
        content_parts.append(f"### {qa.get('question')}\n{qa.get('answer')}")
    content = "\n\n".join(content_parts)
    if len(content) < 50:
        content = (content + "\n\n" + (context or topic) * 3)[:400]
    score = calculate_seo_score(
        SEOScoreRequest(
            title=title[:120],
            meta_description=meta_desc[:320],
            content=content,
            url=url,
        )
    ).model_dump()
    meta = generate_meta_tags(
        MetaTagsRequest(title=title[:120], description=meta_desc[:320], url=url, site_name=topic)
    ).model_dump()
    return {
        "aeo": aeo,
        "seo": {
            "title": title,
            "meta_description": meta_desc,
            "keywords": keywords,
            "canonical": url,
            "html_tags": meta,
            "score": score,
        },
        "content_draft": content,
    }


def _merge_ollama(base: Dict[str, Any], llm: Dict[str, Any]) -> Dict[str, Any]:
    aeo = dict(base["aeo"])
    seo = dict(base["seo"])
    title = (llm.get("title") or seo.get("title") or "").strip()
    meta = (llm.get("meta_description") or seo.get("meta_description") or "").strip()
    summary = (llm.get("summary") or aeo.get("summary") or "").strip()
    if title:
        aeo["suggested_title"] = title
        seo["title"] = title[:70]
    if summary:
        aeo["summary"] = summary
    if meta:
        seo["meta_description"] = meta[:320]
    kws = llm.get("keywords") or []
    if isinstance(kws, list) and kws:
        seo["keywords"] = [str(k).strip() for k in kws if str(k).strip()][:12]
    h2 = llm.get("h2") or []
    if isinstance(h2, list) and h2:
        aeo["structured_sections"] = [str(h).strip() for h in h2 if str(h).strip()][:8]
    faqs = llm.get("faq") or []
    parsed_faq = []
    if isinstance(faqs, list):
        for item in faqs:
            if not isinstance(item, dict):
                continue
            q = (item.get("question") or item.get("q") or "").strip()
            a = (item.get("answer") or item.get("a") or "").strip()
            if q:
                parsed_faq.append({"question": q, "answer": a})
    if parsed_faq:
        aeo["questions_answers"] = parsed_faq
    entities = llm.get("entities") or []
    if isinstance(entities, list) and entities:
        aeo["key_entities"] = [str(e).strip() for e in entities if str(e).strip()][:12]
    tips = llm.get("tips") or []
    if isinstance(tips, list) and tips:
        aeo["tips"] = [str(t).strip() for t in tips if str(t).strip()][:8]
    if title and meta:
        seo["html_tags"] = generate_meta_tags(
            MetaTagsRequest(
                title=seo["title"][:120],
                description=seo["meta_description"][:320],
                url=seo.get("canonical"),
                site_name=title,
            )
        ).model_dump()
    content_parts = [aeo.get("summary") or ""]
    content_parts.extend(f"## {h}" for h in (aeo.get("structured_sections") or []))
    for qa in aeo.get("questions_answers") or []:
        content_parts.append(f"### {qa.get('question')}\n{qa.get('answer')}")
    content = "\n\n".join(p for p in content_parts if p).strip()
    if len(content) >= 50:
        seo["score"] = calculate_seo_score(
            SEOScoreRequest(
                title=(seo.get("title") or "Untitled")[:120],
                meta_description=(seo.get("meta_description") or content[:160])[:320],
                content=content,
                url=seo.get("canonical"),
            )
        ).model_dump()
        base["content_draft"] = content
    base["aeo"] = aeo
    base["seo"] = seo
    return base


async def generate_pack(
    topic: str,
    url: Optional[str] = None,
    business_name: Optional[str] = None,
    context: Optional[str] = None,
    locale: str = "en",
) -> Dict[str, Any]:
    topic = (topic or business_name or url or "Untitled").strip()
    facts = " | ".join(x for x in (business_name, url, context) if x)
    health = await check_ollama_health()
    pack = _heuristic_pack(topic, facts or context, url)
    backend = "heuristic"
    llm = None
    if health.get("status") == "ok":
        llm = await _ollama_pack(topic, facts, locale or "en")
        if llm:
            pack = _merge_ollama(pack, llm)
            backend = "ollama"
    tree = build_tree(topic, pack["aeo"], pack["seo"])
    resume = f"{topic}\n" + "\n".join(_resume_lines(tree))
    return {
        "ok": True,
        "topic": topic,
        "url": url,
        "business_name": business_name,
        "backend": backend,
        "model": settings.OLLAMA_MODEL if backend == "ollama" else None,
        "ollama": health,
        "tree": tree,
        "resume": resume,
        "aeo": pack["aeo"],
        "seo": pack["seo"],
        "content_draft": pack.get("content_draft"),
    }
