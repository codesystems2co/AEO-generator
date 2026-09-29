"""Payable catalog assistant. Optional until the order line is confirmed."""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

PRODUCT_NAME = "Product Catalog AEO and SEO pack With IA"
_MARKER = PRODUCT_NAME.lower()


def catalog_offer(
    order_lines: Sequence[str],
    host: Optional[str],
    platforms: Sequence[str],
) -> Dict[str, Any]:
    blob = " ".join(str(line or "") for line in order_lines).lower()
    owned = _MARKER in blob
    return {
        "product": PRODUCT_NAME,
        "optional": True,
        "payable": True,
        "owned": owned,
        "host": host or None,
        "platforms": [str(p) for p in platforms if p],
    }


def queue_window(pending: Sequence[Dict[str, Any]], active_id: Any, limit: int = 6) -> List[Dict[str, Any]]:
    window: List[Dict[str, Any]] = []
    for row in list(pending)[:limit]:
        item = dict(row)
        item["state"] = "analyzing" if item.get("id") == active_id else "queued"
        window.append(item)
    return window


def advance_queue(pending: Sequence[Dict[str, Any]], analyzed_id: Any) -> List[Dict[str, Any]]:
    return [dict(row) for row in pending if row.get("id") != analyzed_id]


def block_caption(block_index: int, block_size: int = 20, total: Optional[int] = None) -> str:
    index = max(1, int(block_index or 1))
    size = max(1, int(block_size or 20))
    start = (index - 1) * size + 1
    end = index * size
    if total is not None:
        end = min(end, int(total))
    return f"bloque {index}, productos {start}–{end}"


def queue_snapshot(
    pending: Sequence[Dict[str, Any]],
    active_id: Any,
    phase: str = "analyzing",
    block_index: int = 1,
    block_size: int = 20,
    total: Optional[int] = None,
    limit: int = 6,
) -> Dict[str, Any]:
    window: List[Dict[str, Any]] = []
    for row in list(pending)[:limit]:
        item = dict(row)
        if item.get("id") == active_id:
            item["state"] = "analyzed" if phase == "analyzed" else "analyzing"
        else:
            item["state"] = "queued"
        window.append(item)
    return {
        "window": window,
        "caption": block_caption(block_index, block_size, total),
        "analyzing": sum(1 for row in window if row.get("state") == "analyzing"),
    }
