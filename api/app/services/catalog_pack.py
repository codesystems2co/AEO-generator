"""Catalog pack for one existing product. Questions stay on that product URL."""
from __future__ import annotations

import json
import re
from typing import Any, Dict, List

from app.services.aeo_block import render_faq_html

_SKIP = {
    "para", "como", "esta", "este", "estos", "estas", "desde", "donde", "sobre",
    "with", "that", "this", "from", "your", "their", "into",
}


def _clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _sentence(text: str) -> str:
    part = re.split(r"(?<=[.!?])\s+", text.strip(), maxsplit=1)[0]
    return part.strip()


def _fit(text: str, low: int, high: int, extra: str) -> str:
    value = _clean(text)
    if len(value) < low:
        value = _clean(f"{value} {extra}")
    if len(value) < low:
        value = (value + (" " + extra))[:high]
    return value[:high]


def _keywords(name: str, description: str) -> List[str]:
    words = re.findall(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9]{4,}", f"{name} {description}")
    out: List[str] = []
    seen = set()
    for word in words:
        key = word.lower()
        if key in _SKIP or key in seen:
            continue
        seen.add(key)
        out.append(word)
        if len(out) == 8:
            break
    return out


def _faq(name: str, lead: str, locale: str) -> List[Dict[str, str]]:
    if str(locale).lower().startswith("en"):
        return [
            {"question": f"What does {name} include?", "answer": lead},
            {"question": f"Who is {name} for?", "answer": f"{name} is for the shop that buys this offer. {lead}"},
        ]
    return [
        {"question": f"¿Qué incluye {name}?", "answer": lead},
        {"question": f"¿Para quién es {name}?", "answer": f"{name} está dirigido a quien contrata esta oferta. {lead}"},
    ]


def faq_html(faq: List[Dict[str, str]], schema: Dict[str, Any] | None = None) -> str:
    return render_faq_html(faq, schema)


def build_pack(product: Dict[str, Any], locale: str = "es") -> Dict[str, Any]:
    name = _clean(product.get("name"))
    if not name:
        raise ValueError("product name required")
    url = _clean(product.get("url"))
    if not url:
        raise ValueError("product url required")
    description = _clean(product.get("description"))
    lead = _sentence(description) or name
    title = _fit(f"{name}. {lead}", 30, 60, "oferta del comercio")
    meta = _fit(description or lead, 120, 160, "La ficha conserva su dirección y su precio.")
    faq = _faq(name, lead, locale)
    price = product.get("price")
    schema: Dict[str, Any] = {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": name,
        "description": meta,
        "url": url,
    }
    if price is not None:
        schema["offers"] = {
            "@type": "Offer",
            "price": price,
            "priceCurrency": product.get("currency") or "USD",
            "url": url,
        }
    return {
        "product_id": product.get("id"),
        "name": name,
        "price": price,
        "currency": product.get("currency"),
        "seo": {
            "title": title,
            "meta_description": meta,
            "keywords": _keywords(name, description),
            "canonical": url,
        },
        "faq": faq,
        "faq_html": faq_html(faq, schema),
        "schema": schema,
        "source": "heuristic",
    }


def _merge_model(pack: Dict[str, Any], model: Dict[str, Any]) -> Dict[str, Any]:
    seo = dict(pack.get("seo") or {})
    title = _clean(model.get("title"))
    meta = _clean(model.get("meta_description"))
    if 30 <= len(title) <= 60:
        seo["title"] = title
    if 120 <= len(meta) <= 160:
        seo["meta_description"] = meta
    words = model.get("keywords")
    if isinstance(words, list) and words:
        seo["keywords"] = [_clean(word) for word in words if _clean(word)][:8]
    faq_in = model.get("faq")
    faq = pack.get("faq") or []
    if isinstance(faq_in, list) and faq_in:
        built = []
        for item in faq_in:
            if not isinstance(item, dict):
                continue
            question = _clean(item.get("question"))
            answer = _clean(item.get("answer"))
            if question and answer:
                built.append({"question": question, "answer": answer})
        if built:
            faq = built[:2]
    schema = dict(pack.get("schema") or {})
    schema["name"] = pack.get("name")
    schema["description"] = seo.get("meta_description")
    schema["url"] = (pack.get("seo") or {}).get("canonical")
    return {
        **pack,
        "seo": seo,
        "faq": faq,
        "faq_html": faq_html(faq, schema),
        "schema": schema,
        "source": "ollama",
    }


async def with_model(pack: Dict[str, Any], product: Dict[str, Any], locale: str = "es") -> Dict[str, Any]:
    import httpx
    from app.config import settings

    name = _clean(product.get("name"))
    description = _clean(product.get("description"))[:500]
    user = (
        f"Locale: {locale}\nProducto: {name}\nDescripción: {description or name}\n"
        "Devuelve solo JSON con title (30-60), meta_description (120-160), "
        "keywords (lista) y faq (dos objetos question y answer). "
        "No inventes precio ni otra URL."
    )
    payload = {
        "model": settings.OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": "Redactas la ficha de un producto ya existente. JSON únicamente."},
            {"role": "user", "content": user},
        ],
        "stream": False,
        "format": "json",
        "options": {"num_predict": 400, "temperature": 0.2},
    }
    try:
        timeout = httpx.Timeout(25.0, connect=5.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/chat", json=payload)
            response.raise_for_status()
            body = response.json()
            message = (body.get("message") or {}).get("content") or ""
            data = json.loads(message)
    except Exception:
        return pack
    if not isinstance(data, dict):
        return pack
    return _merge_model(pack, data)
