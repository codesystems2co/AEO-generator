"""Write a catalog pack into native product fields, then read it back."""
from __future__ import annotations

from typing import Any, Dict, Optional

from app.services.aeo_block import merge_block
from app.services import catalog_metering

_TARGETS = {
    "odoo": {
        "title": "website_meta_title",
        "meta": "website_meta_description",
        "keywords": "website_meta_keywords",
        "body": "website_description",
    },
    "prestashop": {
        "title": "meta_title",
        "meta": "meta_description",
        "body": "description",
    },
    "woocommerce": {
        # Never overwrite short_description — SEO metas go to Yoast/RankMath keys only.
        "body": "description",
        "yoast_title": "_yoast_wpseo_title",
        "yoast_meta": "_yoast_wpseo_metadesc",
        "rankmath_title": "rank_math_title",
        "rankmath_meta": "rank_math_description",
    },
}


def read_block(shop: Any, offset: int, limit: int = 20):
    if offset < 0 or limit < 1 or limit > 20:
        raise ValueError("catalog block is 1 to 20 rows")
    return shop.read_block(offset, limit)


def _evaluate(before: Dict[str, Any], after: Dict[str, Any], pack: Dict[str, Any]) -> Dict[str, Any]:
    blob = " ".join(str(value) for value in after.values())
    seo = pack.get("seo") or {}
    title = seo.get("title") or ""
    meta = seo.get("meta_description") or ""
    title_bits = [
        after.get(key)
        for key in (
            "website_meta_title",
            "meta_title",
            "_yoast_wpseo_title",
            "rank_math_title",
        )
        if after.get(key)
    ]
    checks = {
        "price": after.get("price") == before.get("price") == pack.get("price"),
        "url": after.get("url") == before.get("url") == seo.get("canonical"),
        "faq": all((item.get("question") or "") in blob for item in pack.get("faq") or []),
        "meta": meta[:80] in blob,
        "title": (title[:40] in " ".join(str(bit) for bit in title_bits)) if title_bits else True,
        "name": after.get("name") == before.get("name"),
    }
    return {"ok": all(checks.values()), "checks": checks}


def native_values(pack: Dict[str, Any], existing_body: str = "") -> Dict[str, str]:
    seo = pack.get("seo") or {}
    keywords = seo.get("keywords") or []
    return {
        "website_meta_title": (seo.get("title") or "")[:70],
        "website_meta_description": (seo.get("meta_description") or "")[:160],
        "website_meta_keywords": ", ".join(str(word) for word in keywords if word)[:200],
        "website_description": merge_block(existing_body or "", pack.get("faq_html") or ""),
    }


def apply_pack(
    shop: Any,
    product_id: Any,
    pack: Dict[str, Any],
    owned: bool,
    *,
    license_key: Optional[str] = None,
    host: Optional[str] = None,
    allowance: Optional[int] = None,
) -> Dict[str, Any]:
    if not owned:
        return {"ok": False, "reason": "optional", "written": []}
    metering_on = license_key is not None and allowance is not None
    already = False
    if metering_on:
        already = catalog_metering.is_processed(license_key, host, product_id)
        if not already and not catalog_metering.can_apply_new(license_key, host, product_id, int(allowance)):
            return {
                "ok": False,
                "reason": "no_credits",
                "written": [],
                "product_id": product_id,
            }
    before = shop.read_product(product_id)
    fields = set(getattr(shop, "fields", ()) or ())
    spec = _TARGETS.get(getattr(shop, "platform", ""), {})
    seo = pack.get("seo") or {}
    values: Dict[str, Any] = {}
    title_key = spec.get("title")
    if title_key and title_key in fields:
        values[title_key] = (seo.get("title") or "")[:70]
    meta_key = spec.get("meta")
    if meta_key and meta_key in fields:
        values[meta_key] = (seo.get("meta_description") or "")[:160]
    keyword_key = spec.get("keywords")
    if keyword_key and keyword_key in fields:
        values[keyword_key] = ", ".join(seo.get("keywords") or [])[:200]
    for meta_key_name in ("yoast_title", "rankmath_title"):
        field = spec.get(meta_key_name)
        if field and field in fields:
            values[field] = (seo.get("title") or "")[:70]
    for meta_key_name in ("yoast_meta", "rankmath_meta"):
        field = spec.get(meta_key_name)
        if field and field in fields:
            values[field] = (seo.get("meta_description") or "")[:160]
    body_key = spec.get("body")
    if body_key and body_key in fields:
        existing = str(before.get(body_key) or before.get("description") or "")
        values[body_key] = merge_block(existing, pack.get("faq_html") or "")
    # Guard: never write product name / price / short_description via this path.
    for forbidden in ("name", "price", "list_price", "short_description"):
        values.pop(forbidden, None)
    shop.write_product(product_id, values)
    # Credit is consumed on successful write of a new id («processed»=applied),
    # even if the post-write evaluate checks are partial.
    if metering_on and not already:
        catalog_metering.record_applied(license_key, host, product_id)
    after = shop.read_product(product_id)
    evaluated = _evaluate(before, after, pack)
    ok = bool(evaluated["ok"])
    return {"ok": ok, "written": list(values), "evaluate": evaluated, "product_id": product_id}
