"""Compare one stored report cycle with the next. No shop secrets."""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

CHECKS = (
    ("connect", "Conexión de la tienda", "Shop connection"),
    ("google", "Propiedad en Google Search", "Google Search property"),
    ("title", "Título del comercio", "Shop title"),
    ("meta", "Meta descripción", "Meta description"),
    ("keywords", "Palabras clave", "Keywords"),
    ("robots", "Archivo robots", "Robots file"),
    ("sitemap", "Mapa del sitio", "Sitemap"),
    ("inject", "Publicado en la tienda", "Published on the shop"),
)

LATER = {
    "es": (
        "Etapa siguiente: Google Merchant y tarjetas de Shopping",
    ),
    "en": (
        "Later stage: Google Merchant and Shopping cards",
    ),
}


def _locale(raw: Any) -> str:
    value = str(raw or "").strip().lower()
    return "en" if value.startswith("en") else "es"


def _label(key: str, locale: str) -> str:
    for item_id, es, en in CHECKS:
        if item_id == key:
            return en if locale == "en" else es
    return key


def _gap_passed_live(google: Dict[str, Any], name: str) -> Optional[bool]:
    for gap in google.get("gaps") or []:
        if (gap.get("name") or "") == name:
            return bool(gap.get("passed")) and not (
                gap.get("virtual_passed") and not gap.get("passed")
            )
    return None


def fingerprint(payload: Optional[Dict[str, Any]]) -> Dict[str, bool]:
    """Public done/open flags for one report. Draft-only gaps stay open."""
    data = payload or {}
    connection = data.get("connection") or {}
    google = data.get("google") or {}
    pack = data.get("pack") or {}
    seo = pack.get("seo") or data.get("seo") or {}
    inject = data.get("inject") or {}
    keywords = seo.get("keywords") or []
    robots = _gap_passed_live(google, "robots.txt")
    sitemap = _gap_passed_live(google, "sitemap.xml")
    flags = {
        "connect": bool(connection.get("connected") or data.get("connect_done")),
        "google": bool(data.get("google_connected") or google.get("step_complete")),
        "title": bool(str(seo.get("title") or "").strip()),
        "meta": bool(str(seo.get("meta_description") or "").strip()),
        "keywords": bool(keywords),
        "inject": bool(inject.get("ok")),
    }
    if robots is not None:
        flags["robots"] = robots
    if sitemap is not None:
        flags["sitemap"] = sitemap
    return flags


def compare_cycles(
    previous: Optional[Dict[str, bool]],
    current: Dict[str, bool],
    locale: Any = "es",
) -> Dict[str, Any]:
    loc = _locale(locale)
    before: List[str] = []
    solved: List[str] = []
    left: List[str] = []
    keys = [item[0] for item in CHECKS if item[0] in current or (previous or {}).get(item[0]) is not None]
    seen = set(keys)
    for item_id, _, _ in CHECKS:
        if item_id not in seen and item_id in current:
            keys.append(item_id)
    for item_id in keys:
        label = _label(item_id, loc)
        was = bool((previous or {}).get(item_id)) if previous else False
        now = bool(current.get(item_id))
        if previous and not was:
            before.append(label)
        if previous and not was and now:
            solved.append(label)
        if not previous and now:
            solved.append(label)
        if not now:
            left.append(label)
    left.extend(LATER[loc])
    still_open = set(left)
    closed = set(solved)
    # A task still open is named once, as work left. A task closed this cycle
    # is named once, under solved. Neither list repeats the other.
    before = [item for item in before if item not in still_open and item not in closed]
    return {
        "first": previous is None,
        "before": before,
        "solved": solved,
        "left": left,
    }


def append_cycle(
    cycles: Optional[Sequence[Dict[str, Any]]],
    fingerprint_row: Dict[str, bool],
    at: str,
) -> List[Dict[str, Any]]:
    rows = [dict(row) for row in (cycles or []) if isinstance(row, dict)]
    if rows and rows[-1].get("fingerprint") == fingerprint_row:
        return rows[-30:]
    rows.append({"at": at, "fingerprint": dict(fingerprint_row)})
    return rows[-30:]
