"""Persist sitemap membership in each shop's own records, then rerun its generator.

Odoo, PrestaShop and WooCommerce rebuild sitemap XML from published records.
A hand-edited XML file is replaced on the next native task. The durable write
is the indexable flag on a record that already exists in the catalog.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence, Tuple
from urllib.parse import urlparse
from xml.sax.saxutils import escape

NATIVE_TASK = {
    "odoo": "website.sitemap",
    "prestashop": "gsitemap-cron",
    "woocommerce": "wp-sitemap",
}

INDEXABLE_KINDS = {
    "odoo": frozenset({"page", "product"}),
    "prestashop": frozenset({"product", "category", "cms"}),
    "woocommerce": frozenset({"product", "page"}),
}


class SitemapUrlError(ValueError):
    """A requested path is not a record of this shop."""


@dataclass(frozen=True)
class IndexRecord:
    path: str
    kind: str
    indexable: bool


@dataclass(frozen=True)
class SitemapShop:
    platform: str
    origin: str
    records: Tuple[IndexRecord, ...]
    file_xml: str


def _path(value: str) -> str:
    raw = (value or "").strip()
    if "://" in raw:
        raw = urlparse(raw).path or "/"
    if not raw.startswith("/"):
        raw = "/" + raw
    if len(raw) > 1:
        raw = raw.rstrip("/")
    return raw or "/"


def _loc(origin: str, path: str) -> str:
    base = (origin or "").rstrip("/")
    return f"{base}{path}"


def _render(origin: str, paths: Sequence[str]) -> str:
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for path in paths:
        loc = escape(_loc(origin, path))
        lines.append(f"<url><loc>{loc}</loc></url>")
    lines.append("</urlset>")
    return "\n".join(lines) + "\n"


def _indexable_paths(shop: SitemapShop) -> Tuple[str, ...]:
    kinds = INDEXABLE_KINDS[shop.platform]
    return tuple(record.path for record in shop.records if record.indexable and record.kind in kinds)


def force_native_task(shop: SitemapShop) -> SitemapShop:
    """Run the commerce sitemap task once. It rewrites file_xml from records."""
    if shop.platform not in NATIVE_TASK:
        raise SitemapUrlError(f"Plataforma no soportada: {shop.platform}")
    xml = _render(shop.origin, _indexable_paths(shop))
    return SitemapShop(
        platform=shop.platform,
        origin=shop.origin,
        records=shop.records,
        file_xml=xml,
    )


def include_existing(shop: SitemapShop, paths: Iterable[str]) -> SitemapShop:
    """Mark catalog records indexable. Unknown paths are refused."""
    wanted = tuple(_path(path) for path in paths)
    known = {record.path: record for record in shop.records}
    missing = [path for path in wanted if path not in known]
    if missing:
        raise SitemapUrlError("La URL no existe en el comercio: " + ", ".join(missing))
    wanted_set = set(wanted)
    updated = tuple(
        IndexRecord(path=record.path, kind=record.kind, indexable=True)
        if record.path in wanted_set
        else record
        for record in shop.records
    )
    return SitemapShop(
        platform=shop.platform,
        origin=shop.origin,
        records=updated,
        file_xml=shop.file_xml,
    )


def _public_records(records: Sequence[IndexRecord]) -> List[Dict[str, object]]:
    return [{"path": record.path, "kind": record.kind, "indexable": record.indexable} for record in records]


def persist_sitemap(shop: SitemapShop, paths: Iterable[str]) -> Dict[str, object]:
    """Update records, then force the native task twice.

    The second run is the commerce cron firing again. Survival means the
    corrected URLs are still in the XML it writes.
    """
    corrected = include_existing(shop, paths)
    once = force_native_task(corrected)
    twice = force_native_task(once)
    wanted = [_path(path) for path in paths]
    missing = [path for path in wanted if _loc(shop.origin, path) not in twice.file_xml]
    return {
        "ok": not missing,
        "platform": shop.platform,
        "native_task": NATIVE_TASK[shop.platform],
        "ran_native_task": 2,
        "survived_second_refresh": not missing,
        "missing": missing,
        "file_xml": twice.file_xml,
        "records": _public_records(twice.records),
    }
