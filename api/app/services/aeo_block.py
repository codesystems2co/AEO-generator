"""Append-only AEO quote block helpers (epic #27).

Never overwrite the client's description. Inject or refresh only the
delimited block. Prefer portable HTML (<details>/<summary>) over JS widgets.
"""
from __future__ import annotations

import html
import json
from typing import Any, Dict, List, Optional, Tuple

START = "<!-- AEO:START v1 -->"
END = "<!-- AEO:END -->"

# Legacy catalog markers still accepted on read/merge so re-inject stays idempotent.
_LEGACY: Tuple[Tuple[str, str], ...] = (
    (START, END),
    ("<!-- aeo-catalog -->", "<!-- /aeo-catalog -->"),
)


def has_injected_block(text: str) -> bool:
    blob = text or ""
    return any(begin in blob and finish in blob for begin, finish in _LEGACY)


def strip_block(text: str) -> str:
    """Remove every known AEO block; keep client text byte-stable otherwise."""
    out = text or ""
    for begin, finish in _LEGACY:
        while begin in out and finish in out:
            pre = out.split(begin, 1)[0].rstrip()
            post = out.split(finish, 1)[1].lstrip()
            out = "\n".join(part for part in (pre, post) if part)
    return out


def merge_block(existing: str, block_html: str) -> str:
    """Replace an existing AEO block in place, or append one at the bottom."""
    inner = (block_html or "").strip()
    block = f"{START}\n{inner}\n{END}"
    text = existing or ""
    for begin, finish in _LEGACY:
        if begin in text and finish in text:
            pre = text.split(begin, 1)[0].rstrip()
            post = text.split(finish, 1)[1].lstrip()
            parts = [part for part in (pre, block, post) if part]
            return "\n".join(parts)
    if text.strip():
        return f"{text.rstrip()}\n{block}"
    return block


def render_faq_html(faq: List[Dict[str, str]], schema: Optional[Dict[str, Any]] = None) -> str:
    """Portable accordion: native <details>/<summary>, optional JSON-LD."""
    parts: List[str] = ['<section class="aeo-quotes" data-aeo="v1">']
    for item in faq or []:
        question = html.escape(str(item.get("question") or "").strip())
        answer = html.escape(str(item.get("answer") or "").strip())
        if not question:
            continue
        parts.append(
            f"<details><summary>{question}</summary><p>{answer}</p></details>"
        )
    if schema:
        payload = html.escape(json.dumps(schema, ensure_ascii=False), quote=False)
        parts.append(f'<script type="application/ld+json">{payload}</script>')
    parts.append("</section>")
    return "".join(parts)


def detect_injection(existing: str) -> Dict[str, Any]:
    """Second-interaction signal for the IA engine / wizard."""
    text = existing or ""
    present = has_injected_block(text)
    return {
        "injected": present,
        "markers": "AEO:START v1" if present else None,
        "client_prefix_len": len(strip_block(text)),
        "action": "refresh_block" if present else "append_block",
    }
