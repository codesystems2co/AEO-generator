"""Spanish AEO coach chat preferring AirLLM, falling back to Ollama."""
from __future__ import annotations

import asyncio
import re
from typing import Any, Dict, List, Optional

import httpx

from app.config import settings
from app.schemas import AEORequest
from app.services.aeo_service import generate_aeo_suggestions

SYSTEM_PROMPT = (
    "Eres un consultor AEO/SEO/GEO en español. Habla claro, breve y preciso.\n"
    "REGLAS OBLIGATORIAS (modelo pequeño — síguelas al pie de la letra):\n"
    "1) Si faltan datos críticos (qué ofrece el negocio, público, diferencial, precios/planes), "
    "haz UNA sola pregunta corta. NO entregues el paquete SEO/AEO completo en el primer turno.\n"
    "2) Cuando el usuario pida un paquete listo para publicar, O cuando ya haya contexto suficiente "
    "(tras 2+ turnos con hechos del negocio), responde SOLO con estas secciones markdown estrictas:\n"
    "   ## Titulo\n"
    "   ## Meta\n"
    "   (máx. 155 caracteres)\n"
    "   ## Keywords\n"
    "   - exactamente N viñetas (usa el N que pida el usuario; si no dice N, 8)\n"
    "   ## H2\n"
    "   - exactamente N viñetas (usa el N pedido; si no dice N, 5)\n"
    "   ## FAQ\n"
    "   - exactamente N pares Pregunta + Respuesta completas (usa el N pedido; si no dice N, 4)\n"
    "3) Reutiliza TODOS los hechos ya dichos en la conversación. No los ignores. "
    "Ejemplos típicos: free trial / prueba gratuita, planes Community y Enterprise, "
    "Odoo + Docker + Kubernetes + facturación IA, PaaS/IaaS.\n"
    "4) Nunca inventes productos, planes ni features no mencionados. Ortografía: PaaS (nunca Paas).\n"
    "5) Sé conciso: sin relleno, sin introducciones largas, sin repetir la pregunta del usuario.\n"
    "6) Si el negocio es Arkiphere Cloud / AnyApp, prioriza: despliegue Odoo con Docker/K8s, "
    "prueba gratuita, Community/Enterprise y facturación IA cuando el usuario los haya citado."
)

SUGGESTIONS_SOFT_TIMEOUT_SEC = 8.0


def _coach_system(messages: List[Dict[str, str]], locale: str = "es") -> str:
    """Build system prompt; first turn uses a tiny ask-only prompt for small models."""
    user_msgs = [
        m for m in (messages or [])
        if (m.get("role") == "user" and (m.get("content") or "").strip())
    ]
    n = len(user_msgs)
    last = (user_msgs[-1].get("content") or "").lower() if user_msgs else ""
    wants_pack = any(
        k in last
        for k in (
            "paquete",
            "listo para publicar",
            "keywords",
            "meta description",
            "faq",
            "h2",
            "título seo",
            "titulo seo",
        )
    )
    en = bool(locale and locale.lower().startswith("en"))

    if n <= 1 and not wants_pack:
        if en:
            return (
                "You are a brief AEO coach. The user just started. "
                "Reply with ONLY one short clarifying question about their offer, audience, or differentiator. "
                "Do not output title, meta, keywords, H2, or FAQ yet. Max 2 sentences."
            )
        return (
            "Eres un coach AEO breve. El usuario acaba de empezar. "
            "Responde SOLO con UNA pregunta corta sobre su oferta, público objetivo o diferencial. "
            "NO escribas título, meta, keywords, H2 ni FAQ todavía. Máximo 2 frases."
        )

    base = SYSTEM_PROMPT
    if en:
        base = (
            "You are a concise AEO/SEO/GEO consultant.\n"
            "RULES: (1) If critical business facts are missing, ask ONE short clarifying question — "
            "do NOT dump a full SEO pack on turn 1. "
            "(2) When the user asks for a publish-ready pack OR after enough context, output STRICT "
            "markdown sections: Title, Meta (max 155 chars), Keywords (exactly N bullets), "
            "H2 (exactly N), FAQ (exactly N Q+A with answers). "
            "(3) Reuse ALL facts already in the conversation (free trial, Community/Enterprise, "
            "Odoo+Docker+K8s+AI billing). (4) Never invent unrelated products. Spell PaaS correctly. "
            "(5) Keep answers concise for small models."
        )

    if wants_pack:
        def _n(pat: str, default: int) -> str:
            m = re.search(pat, last)
            return m.group(1) if m else str(default)

        nk = _n(r"(\d+)\s*keywords?", 8)
        nh = _n(r"(\d+)\s*h2", 5)
        nq = _n(r"(\d+)\s*faq", 4)
        if en:
            return (
                base
                + f"\n\nOUTPUT NOW: Title | Meta (<=155) | Keywords ({nk} bullets) | "
                f"H2 ({nh} short titles only) | FAQ ({nq} Q+A with full answers). "
                "Reuse free trial/Community/Enterprise/Odoo/Docker/K8s/AI billing if already said. No intro."
            )
        return (
            base
            + "\n\nESTADO: paquete publicable ahora. Markdown exacto: "
            f"## Titulo | ## Meta (<=155 chars) | ## Keywords ({nk} viñetas) | "
            f"## H2 ({nh} títulos cortos) | ## FAQ ({nq} pares **P:** / **R:** con respuesta). "
            "Incluye free trial, Community, Enterprise, Odoo, Docker, Kubernetes y facturación IA "
            "si ya se dijeron. Sin introducción. Ortografía PaaS."
        )

    if n >= 2:
        extra = (
            "\n\nAlready have context: draft a brief pack reusing stated facts "
            "(free trial, Community/Enterprise, Odoo+Docker+K8s+AI)."
            if en
            else
            "\n\nYa hay contexto: propone un borrador breve reutilizando hechos ya dados "
            "(free trial, Community/Enterprise, Odoo+Docker+K8s+IA). "
            "Si falta un dato clave, UNA pregunta corta al final."
        )
        return base + extra
    return base


def _derive_topic(messages: List[Dict[str, str]], business_name: Optional[str], url: Optional[str]) -> str:
    if business_name and business_name.strip():
        return business_name.strip()
    for m in reversed(messages or []):
        if m.get("role") == "user" and (m.get("content") or "").strip():
            text = m["content"].strip()
            if len(text) <= 80:
                return text
            return text[:80]
    if url:
        return url
    return "negocio local"


def _should_attach_suggestions(reply: str, messages: List[Dict[str, str]]) -> bool:
    user_turns = sum(1 for m in messages if m.get("role") == "user")
    markers = ("título", "titulo", "meta", "keyword", "h2", "faq", "esquema", "propuesta")
    low = (reply or "").lower()
    if any(k in low for k in markers):
        return True
    return user_turns >= 2



async def check_airllm_health() -> Dict[str, Any]:
    base = settings.AIRLLM_BASE_URL.rstrip("/")
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(f"{base}/health")
            r.raise_for_status()
            data = r.json() if r.content else {}
            return {
                "status": "ok" if data.get("status") == "ok" else "error",
                "airllm": base,
                "model": data.get("model"),
                "loaded": data.get("loaded"),
                "raw": data,
            }
    except Exception as e:
        return {"status": "error", "airllm": base, "error": str(e)[:200]}


async def _airllm_chat(
    messages: List[Dict[str, str]],
    business_name: Optional[str] = None,
    url: Optional[str] = None,
    locale: str = "es",
) -> Optional[str]:
    """Call AirLLM /api/chat; return reply text or None on failure."""
    base = settings.AIRLLM_BASE_URL.rstrip("/")
    timeout = httpx.Timeout(float(getattr(settings, "AIRLLM_TIMEOUT_SEC", 180.0)), connect=5.0)
    payload = {
        "messages": messages,
        "business_name": business_name,
        "url": url,
        "locale": locale,
    }
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.post(f"{base}/api/chat", json=payload)
            r.raise_for_status()
            data = r.json()
            reply = (data.get("reply") or "").strip()
            return reply or None
    except Exception:
        return None


async def _ollama_chat(messages: List[Dict[str, str]], locale: str = "es") -> str:
    base = settings.OLLAMA_BASE_URL.rstrip("/")
    model = settings.OLLAMA_MODEL
    sys = _coach_system(messages, locale=locale)

    ollama_messages = [{"role": "system", "content": sys}]
    for m in messages:
        role = m.get("role") or "user"
        if role not in ("user", "assistant", "system"):
            role = "user"
        content = (m.get("content") or "").strip()
        if content:
            ollama_messages.append({"role": role, "content": content})

    ollama_options = {"num_predict": 500}
    timeout = httpx.Timeout(120.0, connect=10.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            r = await client.post(
                f"{base}/api/chat",
                json={
                    "model": model,
                    "messages": ollama_messages,
                    "stream": False,
                    "options": ollama_options,
                },
            )
            r.raise_for_status()
            data = r.json()
            msg = data.get("message") or {}
            content = msg.get("content") or data.get("response") or ""
            if content.strip():
                return content.strip()
        except Exception:
            pass

        prompt_parts = [sys, ""]
        for m in ollama_messages[1:]:
            prompt_parts.append(f"{m['role'].upper()}: {m['content']}")
        prompt_parts.append("ASSISTANT:")
        prompt = chr(10).join(prompt_parts)
        r = await client.post(
            f"{base}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": ollama_options,
            },
        )
        r.raise_for_status()
        data = r.json()
        return (data.get("response") or "").strip()


async def check_ollama_health() -> Dict[str, Any]:
    base = settings.OLLAMA_BASE_URL.rstrip("/")
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            r = await client.get(f"{base}/api/tags")
            r.raise_for_status()
            data = r.json()
            models = [m.get("name") for m in data.get("models", []) if m.get("name")]
            return {
                "status": "ok",
                "ollama": base,
                "model": settings.OLLAMA_MODEL,
                "models": models,
            }
    except Exception as e:
        return {
            "status": "error",
            "ollama": base,
            "model": settings.OLLAMA_MODEL,
            "error": str(e)[:200],
        }


async def _suggestions_with_soft_timeout(
    topic: str,
    business_name: Optional[str],
    url: Optional[str],
) -> Optional[Dict[str, Any]]:
    """Best-effort AEO suggestions; never block the chat reply for long."""

    def _run():
        aeo = generate_aeo_suggestions(
            AEORequest(
                topic=topic,
                context=url or business_name,
                include_qa=True,
                include_entities=True,
            )
        )
        return aeo.model_dump()

    try:
        return await asyncio.wait_for(
            asyncio.to_thread(_run),
            timeout=SUGGESTIONS_SOFT_TIMEOUT_SEC,
        )
    except Exception:
        return None


async def chat(
    messages: List[Dict[str, str]],
    business_name: Optional[str] = None,
    url: Optional[str] = None,
    locale: Optional[str] = "es",
) -> Dict[str, Any]:
    msgs = [dict(m) for m in (messages or [])]
    if msgs and (business_name or url):
        extra = []
        if business_name:
            extra.append(f"Negocio: {business_name}")
        if url:
            extra.append(f"URL: {url}")
        hint = " | ".join(extra)
        for i in range(len(msgs) - 1, -1, -1):
            if msgs[i].get("role") == "user":
                base_c = msgs[i].get("content", "")
                msgs[i] = {**msgs[i], "content": f"{base_c}\n({hint})".strip()}
                break

    backend = "ollama"
    reply = ""
    prefer_airllm = bool(getattr(settings, "AIRLLM_ENABLED", False))
    if prefer_airllm:
        health = await check_airllm_health()
        if health.get("status") == "ok":
            air = await _airllm_chat(
                msgs,
                business_name=business_name,
                url=url,
                locale=locale or "es",
            )
            if air:
                reply = air
                backend = "airllm"
    if not reply:
        reply = await _ollama_chat(msgs, locale=locale or "es")
        backend = "ollama"
    result: Dict[str, Any] = {"reply": reply, "backend": backend}

    if _should_attach_suggestions(reply, msgs):
        topic = _derive_topic(msgs, business_name, url)
        suggestions = await _suggestions_with_soft_timeout(topic, business_name, url)
        if suggestions is not None:
            result["suggestions"] = suggestions

    return result
