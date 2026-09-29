"""Professional A4 PDF of the Optimizator job dossier."""
from __future__ import annotations

import os
from datetime import datetime, timezone
from io import BytesIO
from typing import Any, Dict, List, Optional

from reportlab.lib.colors import HexColor, white
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Flowable,
    KeepTogether,
    ListFlowable,
    ListItem,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.services.i18n_copy import locale_of, t

NAVY = HexColor("#102033")
TEAL = HexColor("#0f766e")
TEAL_BRIGHT = HexColor("#14b8a6")
SLATE = HexColor("#1e293b")
MUTED = HexColor("#64748b")
LINE = HexColor("#e2e8f0")
SOFT = HexColor("#f4f7fa")
OK = HexColor("#059669")
WAIT = HexColor("#d97706")
FAIL = HexColor("#dc2626")
INFO = HexColor("#0284c7")

STATUS_FILL = {
    "done": OK,
    "pending": WAIT,
    "warn": FAIL,
    "info": INFO,
}

ICON_GLYPH = {
    "order": "P",
    "plug": "C",
    "search": "G",
    "chat": "A",
    "tag": "S",
    "upload": "I",
    "file": "F",
    "info": "i",
}


def _fonts() -> Dict[str, str]:
    regular = "Helvetica"
    bold = "Helvetica-Bold"
    for path, name, bname in (
        ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "DejaVuSans", "DejaVuSans-Bold"),
        ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "DejaVuSans-Bold", "DejaVuSans-Bold"),
    ):
        if os.path.exists(path) and name == "DejaVuSans":
            try:
                pdfmetrics.registerFont(TTFont("DejaVuSans", path))
                regular = "DejaVuSans"
            except Exception:
                pass
        if os.path.exists(path) and name == "DejaVuSans-Bold":
            try:
                pdfmetrics.registerFont(TTFont("DejaVuSans-Bold", path))
                bold = "DejaVuSans-Bold"
            except Exception:
                pass
    bold_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    if regular == "DejaVuSans" and os.path.exists(bold_path):
        try:
            pdfmetrics.registerFont(TTFont("DejaVuSans-Bold", bold_path))
            bold = "DejaVuSans-Bold"
        except Exception:
            bold = "Helvetica-Bold"
    return {"regular": regular, "bold": bold}


def _logo_path() -> Optional[str]:
    here = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(here, "..", "assets", "arkiphere-logo.png"),
        "/app/app/assets/arkiphere-logo.png",
        os.path.join(here, "..", "..", "..", "frontend", "public", "arkiphere-logo.png"),
    ]
    for path in candidates:
        resolved = os.path.abspath(path)
        if os.path.isfile(resolved):
            return resolved
    return None


class StatusDot(Flowable):
    def __init__(self, status: str = "info", size: float = 7):
        super().__init__()
        self.status = status or "info"
        self.size = size
        self.width = size + 2
        self.height = size

    def draw(self):
        color = STATUS_FILL.get(self.status, INFO)
        self.canv.setFillColor(color)
        self.canv.circle(self.size / 2, self.size / 2, self.size / 2, fill=1, stroke=0)
        if self.status == "done":
            self.canv.setStrokeColor(white)
            self.canv.setLineWidth(1.1)
            self.canv.line(1.6, 3.2, 3.0, 1.6)
            self.canv.line(3.0, 1.6, 6.1, 5.4)


class IconBadge(Flowable):
    def __init__(self, icon: str = "info", size: float = 14):
        super().__init__()
        self.icon = icon or "info"
        self.size = size
        self.width = size
        self.height = size

    def draw(self):
        self.canv.setFillColor(TEAL)
        self.canv.roundRect(0, 0, self.size, self.size, 3, fill=1, stroke=0)
        self.canv.setFillColor(white)
        self.canv.setFont("Helvetica-Bold", 7)
        glyph = ICON_GLYPH.get(self.icon, "•")
        self.canv.drawCentredString(self.size / 2, 3.4, glyph)


class ProgressBar(Flowable):
    def __init__(self, percent: int, width: float, height: float = 11):
        super().__init__()
        self.percent = max(0, min(100, int(percent or 0)))
        self.width = width
        self.height = height

    def draw(self):
        self.canv.setFillColor(HexColor("#e8eef4"))
        self.canv.roundRect(0, 0, self.width, self.height, 5, fill=1, stroke=0)
        filled = max(0, (self.width - 0.4) * self.percent / 100.0)
        if filled > 0:
            self.canv.setFillColor(TEAL_BRIGHT)
            self.canv.roundRect(0.2, 0.2, filled, self.height - 0.4, 4, fill=1, stroke=0)


def _styles() -> Dict[str, ParagraphStyle]:
    fonts = _fonts()
    base = getSampleStyleSheet()
    return {
        "kicker": ParagraphStyle(
            "Kicker",
            parent=base["Normal"],
            fontName=fonts["bold"],
            fontSize=8,
            textColor=TEAL,
            tracking=1.2,
            spaceAfter=2,
        ),
        "title": ParagraphStyle(
            "DocTitle",
            parent=base["Normal"],
            fontName=fonts["bold"],
            fontSize=18,
            leading=22,
            textColor=NAVY,
            spaceAfter=4,
        ),
        "subtitle": ParagraphStyle(
            "DocSub",
            parent=base["Normal"],
            fontName=fonts["regular"],
            fontSize=10,
            leading=14,
            textColor=MUTED,
            spaceAfter=8,
        ),
        "body": ParagraphStyle(
            "BodyJust",
            parent=base["Normal"],
            fontName=fonts["regular"],
            fontSize=9.5,
            leading=13.5,
            textColor=SLATE,
            alignment=TA_JUSTIFY,
            spaceAfter=8,
        ),
        "h2": ParagraphStyle(
            "SectionH",
            parent=base["Normal"],
            fontName=fonts["bold"],
            fontSize=11,
            leading=14,
            textColor=NAVY,
            spaceBefore=10,
            spaceAfter=6,
        ),
        "meta": ParagraphStyle(
            "Meta",
            parent=base["Normal"],
            fontName=fonts["regular"],
            fontSize=8.5,
            leading=11,
            textColor=SLATE,
        ),
        "meta_label": ParagraphStyle(
            "MetaLabel",
            parent=base["Normal"],
            fontName=fonts["bold"],
            fontSize=7.5,
            textColor=MUTED,
        ),
        "tree_label": ParagraphStyle(
            "TreeLabel",
            parent=base["Normal"],
            fontName=fonts["bold"],
            fontSize=8.5,
            leading=11.5,
            textColor=NAVY,
        ),
        "tree_value": ParagraphStyle(
            "TreeValue",
            parent=base["Normal"],
            fontName=fonts["regular"],
            fontSize=8.2,
            leading=11.2,
            textColor=MUTED,
        ),
        "footer": ParagraphStyle(
            "Footer",
            parent=base["Normal"],
            fontName=fonts["regular"],
            fontSize=7.5,
            textColor=MUTED,
            alignment=TA_LEFT,
        ),
        "footer_right": ParagraphStyle(
            "FooterRight",
            parent=base["Normal"],
            fontName=fonts["regular"],
            fontSize=7.5,
            textColor=MUTED,
            alignment=TA_RIGHT,
        ),
        "li": ParagraphStyle(
            "ListItem",
            parent=base["Normal"],
            fontName=fonts["regular"],
            fontSize=9,
            leading=12.5,
            textColor=SLATE,
        ),
    }


def _esc(text: Any) -> str:
    return (
        str(text or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


class TreeRow(Flowable):
    def __init__(self, node: Dict[str, Any], depth: int, styles: Dict[str, ParagraphStyle], width: float):
        super().__init__()
        self.node = node
        self.depth = depth
        self.styles = styles
        self.width = width
        indent = 8 + depth * 12
        label = Paragraph(_esc(node.get("label") or ""), styles["tree_label"])
        value = Paragraph(_esc(node.get("value") or ""), styles["tree_value"]) if node.get("value") else None
        inner = width - indent - 14
        label.wrap(inner, 800)
        value_h = 0
        if value:
            value.wrap(inner, 800)
            value_h = value.height
        self._label = label
        self._value = value
        self._indent = indent
        self.height = max(12, label.height + value_h + 4)
        self._value_h = value_h

    def draw(self):
        y = self.height - 8
        if self.depth:
            self.canv.setStrokeColor(LINE)
            self.canv.setLineWidth(0.6)
            self.canv.line(self._indent - 8, 2, self._indent - 8, self.height - 2)
            self.canv.line(self._indent - 8, y + 2, self._indent - 2, y + 2)
        StatusDot(self.node.get("status") or "info", 7).drawOn(self.canv, self._indent, y - 2)
        self._label.drawOn(self.canv, self._indent + 12, y - self._label.height + 8)
        if self._value:
            self._value.drawOn(self.canv, self._indent + 12, 2)


def _walk_tree(nodes: List[Dict[str, Any]], styles: Dict[str, ParagraphStyle], width: float, depth: int = 0) -> List[Flowable]:
    rows: List[Flowable] = []
    for node in nodes or []:
        rows.append(TreeRow(node, depth, styles, width))
        kids = node.get("children") or []
        if kids:
            rows.extend(_walk_tree(kids, styles, width, depth + 1))
    return rows


def _header_table(dossier: Dict[str, Any], styles: Dict[str, ParagraphStyle], width: float) -> Table:
    generated = dossier.get("generated_at") or datetime.now(timezone.utc).isoformat()
    try:
        when = datetime.fromisoformat(str(generated).replace("Z", "+00:00")).strftime("%d/%m/%Y %H:%M UTC")
    except Exception:
        when = str(generated)
    cells = [
        [
            Paragraph(t(locale_of(dossier.get("locale")), "pdf.order"), styles["meta_label"]),
            Paragraph(t(locale_of(dossier.get("locale")), "pdf.site"), styles["meta_label"]),
            Paragraph(t(locale_of(dossier.get("locale")), "pdf.date"), styles["meta_label"]),
            Paragraph(t(locale_of(dossier.get("locale")), "pdf.progress"), styles["meta_label"]),
        ],
        [
            Paragraph(_esc(dossier.get("sale_order_name") or "—"), styles["meta"]),
            Paragraph(_esc(dossier.get("host") or dossier.get("site_url") or "—"), styles["meta"]),
            Paragraph(_esc(when), styles["meta"]),
            Paragraph(f"{int((dossier.get('progress') or {}).get('percent') or 0)}%", styles["meta"]),
        ],
    ]
    table = Table(cells, colWidths=[width * 0.22, width * 0.30, width * 0.30, width * 0.18])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), SOFT),
                ("BOX", (0, 0), (-1, -1), 0.4, LINE),
                ("INNERGRID", (0, 0), (-1, -1), 0.3, LINE),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, 0), 6),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 1),
                ("TOPPADDING", (0, 1), (-1, 1), 1),
                ("BOTTOMPADDING", (0, 1), (-1, 1), 8),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    return table


def _legend(styles: Dict[str, ParagraphStyle], width: float, locale: str = "es") -> Table:
    def cell(status: str, label: str) -> List[Any]:
        return [StatusDot(status, 7), Paragraph(label, styles["tree_value"])]

    loc = locale_of(locale)
    data = [cell("done", t(loc, "pdf.done")) + cell("pending", t(loc, "pdf.pending")) + cell("warn", t(loc, "pdf.warn")) + cell("info", t(loc, "pdf.note"))]
    table = Table(data, colWidths=[10, width / 4 - 10, 10, width / 4 - 10, 10, width / 4 - 10, 10, width / 4 - 10])
    table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 2),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]
        )
    )
    return table


def _draw_chrome(canvas, doc, dossier: Dict[str, Any]):
    canvas.saveState()
    width, height = A4
    canvas.setFillColor(NAVY)
    canvas.rect(0, height - 22 * mm, width, 22 * mm, fill=1, stroke=0)
    canvas.setFillColor(TEAL_BRIGHT)
    canvas.rect(0, height - 23.4 * mm, width, 1.4 * mm, fill=1, stroke=0)
    text_x = 18 * mm
    logo = _logo_path()
    if logo:
        try:
            canvas.drawImage(
                logo,
                18 * mm,
                height - 19.5 * mm,
                width=22,
                height=12,
                mask="auto",
                preserveAspectRatio=True,
                anchor="w",
            )
            text_x = 18 * mm + 26
        except Exception:
            text_x = 18 * mm
    canvas.setFillColor(white)
    canvas.setFont("Helvetica-Bold", 11)
    canvas.drawString(text_x, height - 12 * mm, "Search Engine Optimizator")
    canvas.setFont("Helvetica", 8)
    loc = locale_of(dossier.get("locale"))
    canvas.drawString(text_x, height - 17.2 * mm, t(loc, "pdf.kicker"))
    order = dossier.get("sale_order_name") or ""
    canvas.setFont("Helvetica", 8)
    canvas.drawRightString(width - 18 * mm, height - 12 * mm, str(order))
    canvas.setFillColor(SOFT)
    canvas.rect(0, 0, width, 14 * mm, fill=1, stroke=0)
    canvas.setFillColor(MUTED)
    canvas.setFont("Helvetica", 7.5)
    canvas.drawString(18 * mm, 6 * mm, t(loc, "pdf.footer"))
    canvas.drawRightString(width - 18 * mm, 6 * mm, t(loc, "pdf.page", page=doc.page))
    canvas.restoreState()


def _changelog_bullets(styles: Dict[str, ParagraphStyle], lines: List[str]) -> List[Any]:
    if not lines:
        return [Paragraph("—", styles["body"])]
    bullets = [
        ListItem(Paragraph(_esc(line), styles["li"]), leftIndent=8, bulletColor=NAVY)
        for line in lines
    ]
    return [ListFlowable(bullets, bulletType="bullet", start="circle", leftIndent=12, spaceAfter=4)]


def _changelog_story(changelog: Dict[str, Any], styles: Dict[str, ParagraphStyle], loc: str) -> List[Any]:
    story: List[Any] = [
        Paragraph(t(loc, "pdf.changelog"), styles["h2"]),
        Paragraph(t(loc, "pdf.changelogIntro"), styles["subtitle"]),
    ]
    if changelog.get("first"):
        story.append(Paragraph(t(loc, "pdf.changelogFirst"), styles["body"]))
    before = list(changelog.get("before") or [])
    solved = list(changelog.get("solved") or [])
    left = list(changelog.get("left") or [])
    if before:
        story.append(Paragraph(t(loc, "pdf.unsolvedBefore"), styles["h2"]))
        story.extend(_changelog_bullets(styles, before))
    if solved:
        story.append(Paragraph(t(loc, "pdf.solvedToday"), styles["h2"]))
        story.extend(_changelog_bullets(styles, solved))
    story.append(Paragraph(t(loc, "pdf.left"), styles["h2"]))
    story.extend(_changelog_bullets(styles, left))
    return story


def _reading_story(reading: Dict[str, Any], styles: Dict[str, ParagraphStyle], loc: str) -> List[Any]:
    paragraph = str((reading or {}).get("summary") or "").strip()
    if not reading or not reading.get("ready") or not paragraph:
        return []
    return [
        Paragraph(t(loc, "pdf.reading"), styles["h2"]),
        Paragraph(_esc(paragraph), styles["body"]),
    ]


def render_job_pdf(dossier: Dict[str, Any]) -> bytes:
    buffer = BytesIO()
    styles = _styles()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=28 * mm,
        bottomMargin=18 * mm,
        title=f"{t(locale_of(dossier.get('locale')), 'pdf.title')} {dossier.get('sale_order_name') or ''}".strip(),
        author="Search Engine Optimizator",
    )
    loc = locale_of(dossier.get("locale"))
    width = A4[0] - 36 * mm
    progress = dossier.get("progress") or {}
    percent = int(progress.get("percent") or 0)
    story: List[Any] = []
    story.append(Paragraph(t(loc, "pdf.titleKicker"), styles["kicker"]))
    story.append(Paragraph(t(loc, "pdf.title"), styles["title"]))
    story.append(Paragraph(t(loc, "pdf.subtitle"), styles["subtitle"]))
    story.append(_header_table(dossier, styles, width))
    story.append(Spacer(1, 8))
    story.append(ProgressBar(percent, width, 12))
    story.append(Spacer(1, 5))
    story.append(_legend(styles, width, loc))
    story.append(Paragraph(t(loc, "pdf.clientSummary"), styles["h2"]))
    story.append(Paragraph(_esc(dossier.get("summary") or ""), styles["body"]))

    items = progress.get("items") or []
    if items:
        story.append(Paragraph(t(loc, "pdf.progressByStage"), styles["h2"]))
        bullets = []
        for item in items:
            mark = t(loc, "pdf.done") if item.get("done") else t(loc, "pdf.pending")
            bullets.append(
                ListItem(
                    Paragraph(
                        f"<b>{_esc(item.get('label'))}</b> — {_esc(item.get('detail'))} ({mark})",
                        styles["li"],
                    ),
                    leftIndent=8,
                    bulletColor=OK if item.get("done") else WAIT,
                )
            )
        story.append(ListFlowable(bullets, bulletType="bullet", start="circle", leftIndent=12, spaceAfter=6))

    story.append(Paragraph(t(loc, "pdf.tree"), styles["h2"]))
    story.append(Paragraph(t(loc, "pdf.treeIntro"), styles["subtitle"]))
    tree_block = _walk_tree(dossier.get("tree") or [], styles, width)
    story.extend(tree_block or [Paragraph(t(loc, "pdf.emptyTree"), styles["body"])])

    pack = (dossier.get("payload") or {}).get("pack") or {}
    aeo = pack.get("aeo") or {}
    faqs = aeo.get("questions_answers") or []
    if faqs:
        story.append(Paragraph(t(loc, "pdf.faq"), styles["h2"]))
        for i, qa in enumerate(faqs, 1):
            block = [
                Paragraph(f"<b>{i}. {_esc(qa.get('question') or '')}</b>", styles["tree_label"]),
                Paragraph(_esc(qa.get("answer") or ""), styles["body"]),
            ]
            story.append(KeepTogether(block))

    story.append(Paragraph(t(loc, "pdf.googleAds"), styles["h2"]))
    story.append(Paragraph(t(loc, "pdf.googleAdsBody"), styles["body"]))

    story.append(Paragraph(t(loc, "pdf.notes"), styles["h2"]))
    story.append(Paragraph(t(loc, "pdf.notesBody"), styles["body"]))
    story.extend(_changelog_story(dossier.get("changelog") or {}, styles, loc))
    story.extend(_reading_story(dossier.get("reading") or {}, styles, loc))

    doc.build(
        story,
        onFirstPage=lambda c, d: _draw_chrome(c, d, dossier),
        onLaterPages=lambda c, d: _draw_chrome(c, d, dossier),
    )
    return buffer.getvalue()
