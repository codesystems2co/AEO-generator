"""Catalog report tree and a second PDF bundled with the general report."""
from __future__ import annotations

import zipfile
from io import BytesIO
from typing import Any, Dict, List, Optional

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from app.services.i18n_copy import locale_of
from app.services.pdf_report_service import _draw_chrome, _esc, _styles, _walk_tree

CATALOG_FIELD_NAMES = {
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
        "title": "_yoast_wpseo_title",
        "meta": "_yoast_wpseo_metadesc",
        "body": "description",
        "excerpt": "short_description",
    },
}


def _node(label: str, value: Any = None, children: Optional[List[Dict[str, Any]]] = None, **extra: Any) -> Dict[str, Any]:
    item: Dict[str, Any] = {"label": label, "value": value if value not in (None, "") else None}
    if children:
        item["children"] = children
    item.update(extra)
    return item


def build_catalog_tree(products: List[Dict[str, Any]], complete: bool = True) -> List[Dict[str, Any]]:
    branches: List[Dict[str, Any]] = []
    for product in products:
        pack = product.get("pack") or {}
        seo = pack.get("seo") or {}
        written = product.get("written") or {}
        platform = str(product.get("platform") or "")
        fields = CATALOG_FIELD_NAMES.get(platform, {})
        taxonomy = [
            _node(str(field), term)
            for field, term in written.items()
            if field
        ]
        if not taxonomy:
            for key in ("title", "meta", "keywords", "body"):
                field = fields.get(key)
                if field and (seo.get(key) or seo.get("meta_description") if key == "meta" else None):
                    taxonomy.append(_node(field, seo.get("title") if key == "title" else seo.get("meta_description") if key == "meta" else seo.get(key)))
        faq_nodes = [
            _node(item.get("question") or "", item.get("answer") or "")
            for item in (pack.get("faq") or [])
        ]
        branches.append(
            _node(
                product.get("name") or pack.get("name") or "producto",
                product.get("url") or seo.get("canonical"),
                [
                    _node("descripción", product.get("description")),
                    _node("url", product.get("url") or seo.get("canonical")),
                    _node("seo", seo.get("title"), [
                        _node("title", seo.get("title")),
                        _node("meta_description", seo.get("meta_description")),
                        _node("canonical", seo.get("canonical")),
                    ]),
                    _node("preguntas AEO", None, faq_nodes),
                    _node("taxonomía", None, taxonomy),
                ],
                incomplete=not complete,
                platform=platform,
            )
        )
    return branches


def render_catalog_pdf(dossier: Dict[str, Any]) -> bytes:
    products = list(dossier.get("products") or [])
    complete = bool(dossier.get("complete"))
    locale = locale_of(dossier.get("locale"))
    tree = build_catalog_tree(products, complete=complete)
    styles = _styles()
    buffer = BytesIO()
    names = " ".join(str(item.get("name") or "") for item in products[:4]).strip()
    title = f"Informe de catálogo {names}".strip() if locale != "en" else f"Catalog report {names}".strip()
    if not complete:
        title = f"{title} parcial" if locale != "en" else f"{title} partial"
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=28 * mm,
        bottomMargin=18 * mm,
        title=title,
        author="Search Engine Optimizator",
        subject=title,
    )
    width = A4[0] - 36 * mm
    story: List[Any] = [
        Paragraph("INFORME DE CATÁLOGO" if locale != "en" else "CATALOG REPORT", styles["kicker"]),
        Paragraph("Product Catalog AEO and SEO pack With IA", styles["title"]),
    ]
    if not complete:
        notice = (
            "Informe parcial: solo incluye las fichas ya analizadas."
            if locale != "en"
            else "Partial report: only products already analyzed."
        )
        story.append(Paragraph(notice, styles["subtitle"]))
    story.append(Paragraph(
        "Árbol por producto. El precio es el de la ficha. Las preguntas viven en esa misma URL."
        if locale != "en"
        else "Tree per product. Price stays as stored. Questions stay on that same URL.",
        styles["body"],
    ))
    story.append(Spacer(1, 6))
    story.extend(_walk_tree(tree, styles, width) or [Paragraph("—", styles["body"])])
    chrome = {
        "locale": locale,
        "sale_order_name": dossier.get("sale_order_name"),
        "host": dossier.get("host"),
    }

    def _page(canv, document):
        try:
            canv._doc.compression = 0
        except Exception:
            pass
        _draw_chrome(canv, document, chrome)

    doc.build(story, onFirstPage=_page, onLaterPages=_page)
    return buffer.getvalue()


def bundle_reports(
    general_pdf: bytes,
    catalog_pdf: bytes,
    locale: str = "es",
    order: str = "pedido",
    host: str = "sitio",
) -> bytes:
    loc = locale_of(locale)
    prefix = "report" if loc == "en" else "informe"
    safe_order = (order or ("order" if loc == "en" else "pedido")).replace(" ", "")
    safe_host = (host or ("site" if loc == "en" else "sitio")).replace(" ", "")
    general_name = f"{prefix}-optimizator-{safe_order}-{safe_host}.pdf"
    catalog_name = f"{'catalog-report' if loc == 'en' else 'informe-catalogo'}-{safe_order}-{safe_host}.pdf"
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(general_name, general_pdf)
        archive.writestr(catalog_name, catalog_pdf)
    return buffer.getvalue()
