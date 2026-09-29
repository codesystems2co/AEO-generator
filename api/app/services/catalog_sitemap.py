"""Include a published catalog product through the shop's own sitemap task."""
from __future__ import annotations

from typing import Any, Dict

from app.services.sitemap_persist import persist_sitemap


def include_published_product(shop: Any, product: Dict[str, Any]) -> Dict[str, Any]:
    if not product.get("is_published"):
        return {
            "ok": False,
            "reason": "unpublished",
            "ran_native_task": 0,
            "survived_second_refresh": False,
            "file_xml": getattr(shop, "file_xml", "") or "",
        }
    return persist_sitemap(shop, [product.get("url") or ""])
