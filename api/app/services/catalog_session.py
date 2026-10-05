"""In-memory catalog scan: one product at a time, six visible, blocks of 20."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.services.catalog_apply import apply_pack
from app.services.catalog_offer import advance_queue, queue_snapshot
from app.services.catalog_pack import build_pack
from app.services.catalog_reader import BLOCK_SIZE, BlockSession
from app.services.catalog_report import build_catalog_tree
from app.services.catalog_sitemap import include_published_product

_SESSIONS: Dict[str, Dict[str, Any]] = {}
_RUNS: Dict[str, Dict[str, Any]] = {}


def _key(license_key: str) -> str:
    return (license_key or "").strip()


def get_session(license_key: str) -> Optional[Dict[str, Any]]:
    row = _SESSIONS.get(_key(license_key))
    return dict(row) if isinstance(row, dict) else None


class ListedShop:
    platform = "odoo"
    fields = (
        "website_meta_title",
        "website_meta_description",
        "website_meta_keywords",
        "website_description",
    )

    def __init__(self, rows: List[Dict[str, Any]]):
        self._order = [row.get("id") for row in rows]
        self._rows = {row.get("id"): dict(row) for row in rows}

    def count(self) -> int:
        return len(self._order)

    def fetch(self, offset: int, limit: int) -> List[Dict[str, Any]]:
        chosen = self._order[max(0, offset): max(0, offset) + limit]
        return [dict(self._rows[item]) for item in chosen if item in self._rows]

    def read_product(self, product_id: Any) -> Dict[str, Any]:
        return dict(self._rows.get(product_id) or {})

    def write_product(self, product_id: Any, values: Dict[str, Any]) -> None:
        current = dict(self._rows.get(product_id) or {})
        current.update(values)
        self._rows[product_id] = current


def start_listed(
    license_key: str,
    rows: List[Dict[str, Any]],
    locale: str = "es",
    total: Optional[int] = None,
) -> Dict[str, Any]:
    shop = ListedShop(rows)
    start_session(
        license_key,
        shop,
        owned=True,
        locale=locale,
        batch_ids=[row.get("id") for row in rows],
    )
    state = _SESSIONS.get(_key(license_key)) or {}
    if total and int(total) > int(state.get("total") or 0):
        state["total"] = int(total)
    return public_session(license_key)


def start_session(
    license_key: str,
    shop: Any,
    owned: bool,
    locale: str = "es",
    batch_ids: Optional[List[Any]] = None,
) -> Dict[str, Any]:
    key = _key(license_key)
    reader = BlockSession(shop, BLOCK_SIZE)
    total = reader.start()
    rows, offset = reader.open_block() if total else ([], 0)
    pending = [dict(row) for row in rows]
    active_id = pending[0]["id"] if pending else None
    _SESSIONS[key] = {
        "owned": owned,
        "locale": locale,
        "platform": getattr(shop, "platform", None),
        "reader": reader,
        "shop": shop,
        "pending": pending,
        "analyzed": [],
        "active_id": active_id,
        "phase": "analyzing" if active_id is not None else "idle",
        "block_index": 1,
        "offset": offset,
        "total": total,
        "done": not pending,
        "batch_ids": [item for item in (batch_ids or [])],
    }
    return public_session(key)


def tick_session(license_key: str) -> Dict[str, Any]:
    key = _key(license_key)
    state = _SESSIONS.get(key)
    if not state:
        raise KeyError("catalog session missing")
    if state.get("done"):
        return public_session(key)
    pending: List[Dict[str, Any]] = state["pending"]
    shop = state["shop"]
    locale = state.get("locale") or "es"
    active_id = state.get("active_id")
    current = next((row for row in pending if row.get("id") == active_id), pending[0] if pending else None)
    if current is None:
        state["done"] = True
        return public_session(key)
    product = shop.read_product(current["id"]) if hasattr(shop, "read_product") else dict(current)
    pack = build_pack(product, locale=locale)
    state["analyzed"].append({**product, "pack": pack, "platform": getattr(shop, "platform", product.get("platform"))})
    state["pending"] = advance_queue(pending, current["id"])
    finished = {
        "id": current.get("id"),
        "name": product.get("name"),
        "title": (pack.get("seo") or {}).get("title") or "",
        "source": pack.get("source") or "heuristic",
    }
    state["left"] = ([finished] + list(state.get("left") or []))[:6]
    if not state["pending"]:
        reader: BlockSession = state["reader"]
        reader.close_block()
        if reader.offset < int(state.get("total") or 0):
            rows, offset = reader.open_block()
            state["pending"] = [dict(row) for row in rows]
            state["offset"] = offset
            if rows:
                state["block_index"] = int(state.get("block_index") or 1) + 1
    state["active_id"] = state["pending"][0]["id"] if state["pending"] else None
    state["phase"] = "analyzing" if state["active_id"] is not None else "idle"
    state["done"] = not state["pending"]
    return public_session(key)


def remember_pack(license_key: str, product_id: Any, pack: Dict[str, Any], source: str) -> None:
    state = _SESSIONS.get(_key(license_key))
    if not state:
        return
    saved = dict(pack)
    saved["source"] = source
    for item in state.get("analyzed") or []:
        if item.get("id") == product_id:
            item["pack"] = saved
    for item in state.get("left") or []:
        if item.get("id") == product_id:
            item["title"] = (saved.get("seo") or {}).get("title") or item.get("title")
            item["source"] = source


def publish_fixture(
    license_key: str,
    sitemap_shop: Any = None,
    *,
    host: Optional[str] = None,
    allowance: Optional[int] = None,
) -> Dict[str, Any]:
    key = _key(license_key)
    state = _SESSIONS.get(key)
    if not state:
        raise KeyError("catalog session missing")
    if not state.get("owned"):
        return {"ok": False, "reason": "optional", "written": []}
    shop = state["shop"]
    written = []
    blocked = []
    sitemap = None
    batch_ids = {item for item in (state.get("batch_ids") or [])}
    for item in state.get("analyzed") or []:
        if batch_ids:
            if item.get("id") not in batch_ids:
                continue
        elif str(item.get("name") or "").strip() != "AEO data":
            continue
        result = apply_pack(
            shop,
            item.get("id"),
            item.get("pack") or {},
            owned=True,
            license_key=license_key if allowance is not None else None,
            host=host,
            allowance=allowance,
        )
        item["written"] = {field: (item.get("pack") or {}).get("seo", {}).get("title") for field in result.get("written") or []}
        written.append(result)
        if result.get("reason") == "no_credits":
            blocked.append(item.get("id"))
            continue
        if result.get("ok") and sitemap_shop is not None:
            sitemap = include_published_product(
                sitemap_shop,
                {"url": item.get("url"), "is_published": bool(item.get("is_published", True))},
            )
    ok_rows = [row for row in written if row.get("ok")]
    delivered = bool(ok_rows) and not blocked and all(row.get("ok") for row in written)
    if blocked and not ok_rows:
        state["delivered"] = False
        return {
            "ok": False,
            "reason": "no_credits",
            "written": written,
            "blocked": blocked,
            "blocked_count": len(blocked),
            "sitemap": sitemap,
            "delivered": False,
        }
    state["delivered"] = delivered
    out: Dict[str, Any] = {"ok": delivered, "written": written, "sitemap": sitemap, "delivered": delivered}
    if blocked:
        out["blocked"] = blocked
        out["blocked_count"] = len(blocked)
        out["reason"] = "no_credits"
    return out


def report_ready(license_key: str) -> bool:
    state = _SESSIONS.get(_key(license_key)) or {}
    analyzed = state.get("analyzed") or []
    return bool(state.get("delivered")) and bool(analyzed)


def begin_run(license_key: str, total: int) -> Dict[str, Any]:
    _RUNS[_key(license_key)] = {
        "total": int(total or 0),
        "done": 0,
        "injected": 0,
        "left": [],
        "window": [],
        "active": None,
        "block_index": 1,
        "running": True,
    }
    return run_public(license_key)


def note_window(license_key: str, pending: List[Dict[str, Any]], active_id: Any, block_index: int) -> None:
    state = _RUNS.get(_key(license_key))
    if not state:
        return
    window = []
    for row in list(pending)[:6]:
        window.append({
            "id": row.get("id"),
            "name": row.get("name"),
            "state": "analyzing" if row.get("id") == active_id else "queued",
        })
    state["window"] = window
    state["active"] = active_id
    state["block_index"] = max(1, int(block_index or 1))


def note_finished(license_key: str, item: Dict[str, Any], injected: bool) -> Dict[str, Any]:
    state = _RUNS.get(_key(license_key))
    if not state:
        return {}
    state["done"] = int(state.get("done") or 0) + 1
    if injected:
        state["injected"] = int(state.get("injected") or 0) + 1
    state["left"] = [{
        "id": item.get("id"),
        "name": item.get("name"),
        "title": item.get("title") or "",
        "source": item.get("source") or "heuristic",
    }] + list(state.get("left") or [])
    state["left"] = state["left"][:6]
    total = int(state.get("total") or 0)
    state["running"] = state["done"] < total if total else True
    state["block_index"] = (int(state["done"]) // 20) + 1
    return run_public(license_key)


def mark_injected(license_key: str) -> Dict[str, Any]:
    state = _RUNS.get(_key(license_key))
    if state:
        state["injected"] = int(state.get("injected") or 0) + 1
    return run_public(license_key)


def run_public(license_key: str) -> Dict[str, Any]:
    state = _RUNS.get(_key(license_key)) or {}
    done = int(state.get("done") or 0)
    total = int(state.get("total") or 0)
    block = int(state.get("block_index") or 1)
    start = ((block - 1) * 20) + 1
    end = min(block * 20, total) if total else block * 20
    return {
        "running": bool(state.get("running")),
        "done": done,
        "injected": int(state.get("injected") or 0),
        "total": total,
        "left": list(state.get("left") or []),
        "window": list(state.get("window") or []),
        "caption": f"bloque {block}, productos {start}–{end}",
    }


def public_session(license_key: str) -> Dict[str, Any]:
    state = _SESSIONS.get(_key(license_key)) or {}
    snap = queue_snapshot(
        state.get("pending") or [],
        state.get("active_id"),
        phase=state.get("phase") or "analyzing",
        block_index=int(state.get("block_index") or 1),
        block_size=BLOCK_SIZE,
        total=state.get("total"),
    )
    products = list(state.get("analyzed") or [])
    complete = bool(state.get("done"))
    return {
        "ok": True,
        "owned": bool(state.get("owned")),
        "done": complete,
        "total": state.get("total") or 0,
        "analyzed_count": len(products),
        "queue": snap,
        "left": list(state.get("left") or []),
        "tree": build_catalog_tree(products, complete=complete),
        "products": products,
        "platform": state.get("platform"),
        "incomplete": not complete,
    }
