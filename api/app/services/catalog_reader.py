"""Read a shop catalog in closed offset blocks. Foreign URLs are refused."""
from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple
from urllib.parse import urlparse

BLOCK_SIZE = 20

ODOO_FIELDS = (
    "id",
    "name",
    "description_sale",
    "website_description",
    "website_url",
    "list_price",
    "currency_id",
    "website_meta_title",
    "website_meta_description",
    "website_meta_keywords",
    "is_published",
)

PRESTA_DISPLAY = (
    "id,name,description,description_short,price,link_rewrite,"
    "meta_title,meta_description,active"
)


class BlockOpenError(RuntimeError):
    """The current block must be closed before the next offset is requested."""


class ForeignUrlError(ValueError):
    """The path is not a product already read from this catalog."""


def _path(value: str) -> str:
    raw = (value or "").strip()
    if "://" in raw:
        raw = urlparse(raw).path or "/"
    if not raw.startswith("/"):
        raw = "/" + raw
    if len(raw) > 1:
        raw = raw.rstrip("/")
    return raw or "/"


# All saleable active products/services — no artificial cap; BlockSession pages by 20.
ODOO_CATALOG_DOMAIN = [("sale_ok", "=", True), ("active", "=", True)]


def odoo_count_call() -> Dict[str, Any]:
    return {
        "model": "product.template",
        "method": "search_count",
        "domain": list(ODOO_CATALOG_DOMAIN),
    }


def odoo_fetch_call(offset: int, limit: int) -> Dict[str, Any]:
    return {
        "model": "product.template",
        "method": "search_read",
        "domain": list(ODOO_CATALOG_DOMAIN),
        "fields": list(ODOO_FIELDS),
        "offset": int(offset),
        "limit": int(limit),
        "order": "id asc",
    }


def prestashop_fetch_params(offset: int, limit: int) -> Dict[str, str]:
    return {"limit": f"{int(offset)},{int(limit)}", "display": f"[{PRESTA_DISPLAY}]"}


def woocommerce_fetch_params(offset: int, limit: int) -> Dict[str, int]:
    size = max(1, int(limit))
    page = (max(0, int(offset)) // size) + 1
    return {"per_page": size, "page": page}


def normalize_odoo(row: Dict[str, Any], origin: str = "") -> Dict[str, Any]:
    url = str(row.get("website_url") or "").strip()
    if url and not url.startswith("http"):
        url = f"{origin.rstrip('/')}{url if url.startswith('/') else '/' + url}"
    currency = row.get("currency_id")
    currency_code = currency[1] if isinstance(currency, (list, tuple)) and len(currency) > 1 else row.get("currency")
    return {
        "id": row.get("id"),
        "name": row.get("name"),
        "description": row.get("description_sale") or row.get("website_description") or "",
        "url": url,
        "price": row.get("list_price") if row.get("list_price") not in (False, None) else row.get("price"),
        "currency": currency_code,
        "website_meta_title": row.get("website_meta_title") or "",
        "website_meta_description": row.get("website_meta_description") or "",
        "website_meta_keywords": row.get("website_meta_keywords") or "",
        "website_description": row.get("website_description") or "",
        "is_published": bool(row.get("is_published")),
        "platform": "odoo",
    }


def normalize_prestashop(row: Dict[str, Any], origin: str = "") -> Dict[str, Any]:
    rewrite = str(row.get("link_rewrite") or "").strip()
    ident = row.get("id")
    url = str(row.get("url") or "").strip()
    if not url and rewrite:
        url = f"{origin.rstrip('/')}/{ident}-{rewrite}" if ident else f"{origin.rstrip('/')}/{rewrite}"
    return {
        "id": ident,
        "name": _first_lang(row.get("name")),
        "description": _first_lang(row.get("description") or row.get("description_short")),
        "url": url,
        "price": _num(row.get("price")),
        "currency": row.get("currency"),
        "meta_title": _first_lang(row.get("meta_title")),
        "meta_description": _first_lang(row.get("meta_description")),
        "link_rewrite": rewrite,
        "is_published": str(row.get("active") or "").strip() in ("1", "true", "True", "True"),
        "platform": "prestashop",
    }


def normalize_woocommerce(row: Dict[str, Any]) -> Dict[str, Any]:
    meta = {item.get("key"): item.get("value") for item in (row.get("meta_data") or []) if isinstance(item, dict)}
    return {
        "id": row.get("id"),
        "name": row.get("name"),
        "description": row.get("description") or row.get("short_description") or "",
        "url": row.get("permalink") or row.get("url") or "",
        "price": _num(row.get("price") or row.get("regular_price")),
        "currency": row.get("currency"),
        "short_description": row.get("short_description") or "",
        "_yoast_wpseo_title": meta.get("_yoast_wpseo_title") or row.get("_yoast_wpseo_title"),
        "_yoast_wpseo_metadesc": meta.get("_yoast_wpseo_metadesc") or row.get("_yoast_wpseo_metadesc"),
        "rank_math_title": meta.get("rank_math_title"),
        "rank_math_description": meta.get("rank_math_description"),
        "is_published": str(row.get("status") or "").lower() == "publish",
        "platform": "woocommerce",
    }


def _first_lang(value: Any) -> str:
    if isinstance(value, dict):
        return str(next(iter(value.values()), "") or "")
    if isinstance(value, list) and value:
        first = value[0]
        if isinstance(first, dict):
            return str(first.get("value") or first.get("name") or "")
        return str(first)
    return str(value or "")


def _num(value: Any) -> Optional[float]:
    if value in (None, False, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


class BlockSession:
    def __init__(self, transport: Any, block_size: int = BLOCK_SIZE):
        if block_size < 1 or block_size > BLOCK_SIZE:
            raise ValueError("catalog block is 1 to 20 rows")
        self.transport = transport
        self.block_size = block_size
        self.offset = 0
        self.closed = True
        self.total: Optional[int] = None
        self.current_rows: List[Dict[str, Any]] = []
        self.known_paths: set[str] = set()

    def start(self) -> int:
        self.total = int(self.transport.count() or 0)
        return self.total

    def open_block(self) -> Tuple[List[Dict[str, Any]], int]:
        if not self.closed:
            raise BlockOpenError("current block still open")
        rows = list(self.transport.fetch(self.offset, self.block_size) or [])
        self.current_rows = rows
        for row in rows:
            url = str(row.get("url") or "")
            if url:
                self.known_paths.add(_path(url))
        self.closed = False
        return rows, self.offset

    def close_block(self) -> int:
        if not self.closed:
            self.offset += self.block_size
            self.closed = True
            self.current_rows = []
        return self.offset

    def reject_unknown(self, url: str) -> bool:
        if _path(url) not in self.known_paths:
            raise ForeignUrlError(url)
        return True


class CallableTransport:
    def __init__(self, count_fn: Callable[[], int], fetch_fn: Callable[[int, int], Sequence[Dict[str, Any]]]):
        self._count = count_fn
        self._fetch = fetch_fn

    def count(self) -> int:
        return int(self._count() or 0)

    def fetch(self, offset: int, limit: int) -> List[Dict[str, Any]]:
        return list(self._fetch(offset, limit) or [])
