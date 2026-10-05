"""Pure helpers to seed Paso 3 profile fields from crawled page data."""
from __future__ import annotations

from typing import Any, Dict, Optional


def organization_name_from_ld(node: Any) -> Optional[str]:
    if isinstance(node, list):
        for item in node:
            found = organization_name_from_ld(item)
            if found:
                return found
        return None
    if not isinstance(node, dict):
        return None
    if _is_organization_type(node.get("@type") or node.get("type")):
        name = node.get("name")
        if isinstance(name, str) and name.strip():
            return name.strip()[:180]
    graph = node.get("@graph")
    if graph is not None:
        return organization_name_from_ld(graph)
    return None


def _is_organization_type(kind: Any) -> bool:
    if isinstance(kind, list):
        return any(_is_organization_type(item) for item in kind)
    text = str(kind or "").strip().lower()
    return text in {"organization", "localbusiness", "corporation", "store"}


def seed_remediation_from_page(page: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """When checks already pass, still expose page title/h1/meta for Paso 3 prefill."""
    data = page if isinstance(page, dict) else {}
    title = str(data.get("title") or "").strip()
    meta = str(data.get("meta_description") or "").strip()
    h1_list = data.get("h1_list") or []
    h1 = ""
    if isinstance(h1_list, list) and h1_list:
        h1 = str(h1_list[0] or "").strip()
    org = str(data.get("organization_name") or "").strip()
    og = str(data.get("og_site_name") or "").strip()
    if not (title or meta or h1):
        return {}
    seeded: Dict[str, Any] = {
        "title": title,
        "meta_description": meta,
        "h1": h1,
        "fixes": [],
        "backend": "page",
    }
    if org:
        seeded["organization_name"] = org
    if og:
        seeded["og_site_name"] = og
    return seeded
