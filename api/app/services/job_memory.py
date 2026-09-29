"""Saved job history and the next interaction's reading. No shop secrets."""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from app.services.job_changelog import CHECKS

_ARCHIVE_LIMIT = 12


def _locale(raw: Any) -> str:
    return "en" if str(raw or "").strip().lower().startswith("en") else "es"


def _join(items: Any) -> str:
    if not isinstance(items, list):
        return ""
    clean = [str(item).strip() for item in items if str(item or "").strip()]
    return ", ".join(clean)


def _heading(value: Any) -> str:
    if isinstance(value, dict):
        for key in ("text", "title", "heading", "name"):
            raw = value.get(key)
            if isinstance(raw, str) and raw.strip():
                return raw.strip()
        return ""
    return str(value or "").strip()


def _open_labels(fingerprint: Dict[str, Any], locale: str) -> List[str]:
    loc = _locale(locale)
    labels = []
    for item_id, es, en in CHECKS:
        if item_id in fingerprint and not fingerprint.get(item_id):
            labels.append(en if loc == "en" else es)
    return labels


def public_snapshot(dossier: Dict[str, Any]) -> Dict[str, Any]:
    """Report facts kept for the next interaction. Credentials stay out."""
    payload = dossier.get("payload") if isinstance(dossier.get("payload"), dict) else {}
    pack = payload.get("pack") if isinstance(payload.get("pack"), dict) else {}
    aeo = pack.get("aeo") if isinstance(pack.get("aeo"), dict) else {}
    seo = pack.get("seo") if isinstance(pack.get("seo"), dict) else {}
    inject = payload.get("inject") if isinstance(payload.get("inject"), dict) else {}
    google = payload.get("google") if isinstance(payload.get("google"), dict) else {}
    score = seo.get("score") if isinstance(seo.get("score"), dict) else {}
    questions = []
    for row in (aeo.get("questions_answers") or [])[:8]:
        if isinstance(row, dict) and str(row.get("question") or "").strip():
            questions.append(
                {
                    "question": str(row.get("question")).strip()[:180],
                    "answer": str(row.get("answer") or "").strip()[:320],
                }
            )
    open_gaps = []
    for gap in google.get("gaps") or []:
        if isinstance(gap, dict) and not gap.get("passed"):
            open_gaps.append(str(gap.get("label") or gap.get("name") or "").strip())
    snapshot = {
        "at": dossier.get("generated_at"),
        "order": dossier.get("sale_order_name"),
        "host": dossier.get("host"),
        "fingerprint": dossier.get("fingerprint") or {},
        "changelog": {
            "solved": list((dossier.get("changelog") or {}).get("solved") or []),
            "left": list((dossier.get("changelog") or {}).get("left") or []),
        },
        "progress": (dossier.get("progress") or {}).get("percent"),
        "seo": {
            "title": str(seo.get("title") or "")[:180],
            "meta_description": str(seo.get("meta_description") or "")[:320],
            "keywords": [str(item) for item in (seo.get("keywords") or [])[:12]],
            "score": score.get("overall_score"),
        },
        "aeo": {
            "title": str(aeo.get("suggested_title") or "")[:180],
            "summary": str(aeo.get("summary") or "")[:500],
            "questions": questions,
            "sections": [_heading(item) for item in (aeo.get("structured_sections") or [])[:8] if _heading(item)],
        },
        "inject": {
            "ok": bool(inject.get("ok")),
            "message": str(inject.get("customer_message") or inject.get("message") or "")[:240],
        },
        "google_open": [item for item in open_gaps if item][:12],
        "connected": bool((payload.get("connection") or {}).get("connected") or payload.get("connect_done")),
    }
    return snapshot


def append_archive(archives: Optional[List[Dict[str, Any]]], snapshot: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows = [dict(row) for row in (archives or []) if isinstance(row, dict)]
    if rows and rows[-1].get("fingerprint") == snapshot.get("fingerprint"):
        return rows[-_ARCHIVE_LIMIT:]
    rows.append(dict(snapshot))
    return rows[-_ARCHIVE_LIMIT:]


def previous_work(
    archives: Optional[List[Dict[str, Any]]],
    cycles: Optional[List[Dict[str, Any]]],
    current: Dict[str, Any],
    locale: str,
) -> Optional[Dict[str, Any]]:
    rows = [row for row in (archives or []) if isinstance(row, dict)]
    if rows:
        return rows[-1]
    stored = [row for row in (cycles or []) if isinstance(row, dict)]
    if not stored:
        return None
    last = stored[-1]
    fingerprint = last.get("fingerprint") if isinstance(last.get("fingerprint"), dict) else None
    if not fingerprint:
        return None
    return {
        "at": last.get("at"),
        "fingerprint": fingerprint,
        "changelog": {"left": _open_labels(fingerprint, locale), "solved": []},
        "inject": {"ok": bool(fingerprint.get("inject")), "message": ""},
    }


def cache_key(previous: Optional[Dict[str, Any]], current: Dict[str, Any]) -> str:
    prior = previous.get("fingerprint") if isinstance(previous, dict) else {}
    return json.dumps(["v3", prior or {}, current or {}], sort_keys=True, ensure_ascii=False)


def _work_items(items: Any) -> List[str]:
    rows = []
    for item in items or []:
        text = str(item or "").strip()
        low = text.lower()
        if not text or low.startswith("etapa siguiente") or low.startswith("later stage"):
            continue
        rows.append(text)
    return rows


def heuristic_reading(
    previous: Optional[Dict[str, Any]],
    changelog: Dict[str, Any],
    locale: Any,
) -> Dict[str, Any]:
    loc = _locale(locale)
    solved = _join(_work_items((changelog or {}).get("solved")))
    if not previous:
        summary = (
            "First job stored. The next interaction compares it."
            if loc == "en"
            else "Primer trabajo guardado. La próxima interacción lo compara."
        )
        return {"ready": False, "source": "first", "summary": summary}
    inject = previous.get("inject") if isinstance(previous.get("inject"), dict) else {}
    reason = str(inject.get("message") or "").strip() if not inject.get("ok") else ""
    if loc == "en":
        if solved:
            summary = f"After the other interactions, this visit completed what could not be done before: {solved}."
            if reason:
                summary += f" The earlier reason was: {reason}"
        else:
            summary = "After the other interactions, this visit did not complete anything that was still open."
    elif solved:
        summary = f"Después de otras interacciones, quedó hecho lo que antes no se pudo: {solved}."
        if reason:
            summary += f" El motivo anterior fue: {reason}"
    else:
        summary = "Después de otras interacciones, esta visita no completó nada que siguiera pendiente."
    return {"ready": True, "source": "heuristic", "summary": summary}


def _as_sentence(value: Any) -> str:
    if isinstance(value, list):
        return _join(value)
    text = str(value or "").strip()
    if text.startswith("[") and text.endswith("]"):
        try:
            parsed = json.loads(text.replace("'", '"'))
        except Exception:
            parsed = None
        if isinstance(parsed, list):
            return _join(parsed)
    return text


def _parse_reading(text: str) -> Optional[Dict[str, str]]:
    if not text:
        return None
    raw = text.strip()
    try:
        data = json.loads(raw)
    except Exception:
        start = raw.find("{")
        end = raw.rfind("}")
        if start < 0 or end <= start:
            return None
        try:
            data = json.loads(raw[start : end + 1])
        except Exception:
            return None
    if not isinstance(data, dict):
        return None
    summary = _as_sentence(data.get("summary"))
    if not summary or "[" in summary or "]" in summary:
        return None
    return {"summary": summary[:700]}


async def ollama_reading(
    previous: Dict[str, Any],
    changelog: Dict[str, Any],
    locale: Any,
) -> Optional[Dict[str, str]]:
    import httpx

    from app.config import settings

    loc = _locale(locale)
    language = "English" if loc == "en" else "Spanish"
    closed = _work_items((changelog or {}).get("solved"))
    inject = previous.get("inject") if isinstance(previous.get("inject"), dict) else {}
    reason = str(inject.get("message") or "").strip() if not inject.get("ok") else ""
    system = (
        "Compare the previous saved job with this interaction. "
        "Reply with JSON only: {\"summary\":\"\"}. "
        "summary is one paragraph in the requested language about what this visit completed "
        "that could not be done before. "
        "Use only the tasks in closed_now. When closed_now is empty, say that this visit "
        "completed nothing that was still open. "
        "Mention inject_reason only when closed_now is not empty and a reason is present. "
        "Do not list tasks that remain open. Do not mention later stages. No headings and no brackets."
    )
    user = json.dumps(
        {"language": language, "closed_now": closed, "inject_reason": reason},
        ensure_ascii=False,
    )[:6000]
    payload = {
        "model": settings.OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "stream": False,
        "format": "json",
        "options": {"num_predict": 160, "temperature": 0.2},
    }
    timeout = httpx.Timeout(8.0, connect=3.0)
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/chat", json=payload)
            response.raise_for_status()
            body = response.json()
            message = body.get("message") or {}
            return _parse_reading(message.get("content") or body.get("response") or "")
    except Exception:
        return None


async def build_reading(
    archives: Optional[List[Dict[str, Any]]],
    cycles: Optional[List[Dict[str, Any]]],
    readings: Optional[Dict[str, Any]],
    dossier: Dict[str, Any],
) -> Dict[str, Any]:
    current = dossier.get("fingerprint") if isinstance(dossier.get("fingerprint"), dict) else {}
    changelog = dossier.get("changelog") if isinstance(dossier.get("changelog"), dict) else {}
    locale = dossier.get("locale")
    previous = previous_work(archives, cycles, current, _locale(locale))
    key = cache_key(previous, current)
    cached = (readings or {}).get(key) if isinstance(readings, dict) else None
    if isinstance(cached, dict) and cached.get("summary"):
        return {**cached, "cache_key": key}
    base = heuristic_reading(previous, changelog, locale)
    closed = _work_items((changelog or {}).get("solved"))
    if previous:
        enriched = await ollama_reading(previous, changelog, locale)
        summary = (enriched or {}).get("summary") or ""
        if closed and summary and any(item in summary for item in closed):
            base = {"ready": True, "source": "ollama", "summary": summary}
    base["cache_key"] = key
    return base


def remember_reading(readings: Optional[Dict[str, Any]], reading: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    stored = dict(readings) if isinstance(readings, dict) else {}
    if not isinstance(reading, dict) or not reading.get("cache_key"):
        return stored
    key = str(reading.get("cache_key"))
    stored[key] = {
        "ready": bool(reading.get("ready")),
        "source": reading.get("source") or "heuristic",
        "summary": reading.get("summary") or "",
    }
    if len(stored) > _ARCHIVE_LIMIT:
        for old in list(stored.keys())[: len(stored) - _ARCHIVE_LIMIT]:
            stored.pop(old, None)
    return stored
