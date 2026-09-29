"""Collect wizard work into a client-facing job tree and progress dossier."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

GAP_LABELS = {
    "Live URL fetch": "Página accesible",
    "Title tag": "Título",
    "Meta description": "Descripción",
    "H1 present": "Encabezado principal",
    "robots.txt": "Archivo robots",
    "sitemap.xml": "Mapa del sitio",
    "OAuth client configured": "Search Console listo",
    "Client consent": "Acceso a Search Console",
    "GSC property visible": "Propiedad en Search Console",
    "Service account key": "Cuenta de servicio",
    "GSC property share": "Propiedad compartida",
    "Auth mode selected": "Modo de acceso",
    "Commerce signals": "Señales de tienda",
    "Structured data": "Datos estructurados",
}

from app.services.i18n_copy import GAP_KEYS, locale_of, t
from app.services.pack_service import heading_label

PLATFORM_LABELS = {
    "odoo": "Odoo",
    "prestashop": "PrestaShop",
    "woocommerce": "WooCommerce",
}

SECRET_KEYS = {
    "api_key",
    "ws_key",
    "consumer_secret",
    "consumer_key",
    "password",
    "secret",
    "token",
    "access_token",
    "refresh_token",
    "json_key",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _when(value: Optional[str]) -> str:
    raw = (value or "").strip()
    if not raw:
        return datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC")
    try:
        stamp = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return stamp.strftime("%d/%m/%Y %H:%M UTC")
    except Exception:
        return raw


def _host(url: Optional[str]) -> str:
    raw = (url or "").strip()
    if not raw:
        return ""
    try:
        host = (urlparse(raw if "://" in raw else f"https://{raw}").hostname or "").strip().lower()
    except Exception:
        return raw
    return host[4:] if host.startswith("www.") else host


def _clip(value: Any, limit: int = 420) -> str:
    text = " ".join(str(value or "").split())
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def _node(
    label: str,
    value: Optional[str] = None,
    status: Optional[str] = None,
    children: Optional[List[Dict[str, Any]]] = None,
    icon: Optional[str] = None,
) -> Dict[str, Any]:
    node: Dict[str, Any] = {"label": label}
    if value:
        node["value"] = _clip(value, 500)
    if status:
        node["status"] = status
    if icon:
        node["icon"] = icon
    if children:
        node["children"] = children
    return node


def _status(flag: bool, pending: str = "pending") -> str:
    return "done" if flag else pending


def _strip_secrets(data: Any) -> Any:
    if isinstance(data, dict):
        cleaned: Dict[str, Any] = {}
        for key, value in data.items():
            if str(key).lower() in SECRET_KEYS or "cipher" in str(key).lower() or str(key).lower().endswith("_enc"):
                continue
            if str(key).lower() in {"license", "key"} and isinstance(value, str) and len(value) > 8:
                cleaned[key] = f"…{value[-4:]}"
                continue
            cleaned[key] = _strip_secrets(value)
        return cleaned
    if isinstance(data, list):
        return [_strip_secrets(item) for item in data]
    return data


def _progress_items(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    connection = payload.get("connection") or {}
    google = payload.get("google") or {}
    pack = payload.get("pack") or {}
    inject = payload.get("inject") or {}
    aeo = pack.get("aeo") or payload.get("aeo") or {}
    seo = pack.get("seo") or payload.get("seo") or {}
    loc = locale_of(payload.get("locale"))
    connect_done = bool(connection.get("connected") or payload.get("connect_done"))
    google_done = bool(google.get("step_complete"))
    aeo_done = bool(aeo)
    seo_done = bool(seo)
    has_inject = isinstance(inject, dict) and ("ok" in inject)
    inject_done = bool(inject.get("ok")) if has_inject else False
    report_done = connect_done and google_done and aeo_done and seo_done and has_inject
    return [
        {"id": "connect", "label": t(loc, "progress.connect"), "detail": t(loc, "progress.connectDetail"), "weight": 20, "done": connect_done, "icon": "plug"},
        {"id": "google", "label": t(loc, "progress.google"), "detail": t(loc, "progress.googleDetail"), "weight": 20, "done": google_done, "icon": "search"},
        {"id": "aeo", "label": t(loc, "progress.aeo"), "detail": t(loc, "progress.aeoDetail"), "weight": 20, "done": aeo_done, "icon": "chat"},
        {"id": "seo", "label": t(loc, "progress.seo"), "detail": t(loc, "progress.seoDetail"), "weight": 15, "done": seo_done, "icon": "tag"},
        {"id": "inject", "label": t(loc, "progress.publish"), "detail": t(loc, "progress.publishDetail"), "weight": 20, "done": inject_done, "icon": "upload"},
        {"id": "report", "label": t(loc, "progress.report"), "detail": t(loc, "progress.reportDetail"), "weight": 5, "done": report_done, "icon": "file"},
    ]


def build_progress(payload: Dict[str, Any]) -> Dict[str, Any]:
    items = _progress_items(payload)
    percent = int(sum(item["weight"] for item in items if item["done"]))
    current = next((item for item in items if not item["done"]), items[-1])
    return {
        "percent": min(100, percent),
        "items": items,
        "current_id": current["id"],
        "complete": percent >= 100,
    }


def _gap_children(google: Dict[str, Any], connected: bool, loc: str) -> List[Dict[str, Any]]:
    children: List[Dict[str, Any]] = []
    hidden = {"OAuth client configured", "Service account key", "GSC property share", "Auth mode selected"}
    for gap in google.get("gaps") or []:
        name = gap.get("name") or ""
        if name in hidden:
            continue
        consent = name == "Client consent"
        passed = True if consent and connected else bool(gap.get("virtual_passed") or gap.get("passed"))
        auto = bool(gap.get("virtual_passed") and not gap.get("passed") and not (consent and connected))
        state = t(loc, "gap.auto") if passed and auto else (t(loc, "gap.done") if passed else t(loc, "gap.wait"))
        children.append(
            _node(
                t(loc, GAP_KEYS.get(name, "gap.live")) if name in GAP_KEYS else name,
                state,
                status="done" if passed else "pending",
            )
        )
    return children


def build_tree(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    connection = payload.get("connection") or {}
    google = payload.get("google") or {}
    pack = payload.get("pack") or {}
    inject = payload.get("inject") or {}
    aeo = pack.get("aeo") or payload.get("aeo") or {}
    seo = pack.get("seo") or payload.get("seo") or {}
    platform = (payload.get("platform") or connection.get("platform") or "").strip().lower()
    platform_label = PLATFORM_LABELS.get(platform, platform.title() or "—")
    site = payload.get("site_url") or connection.get("url") or ""
    order = payload.get("sale_order_name") or connection.get("sale_order_name") or "—"
    loc = locale_of(payload.get("locale"))
    google_connected = bool(payload.get("google_connected"))
    faqs = aeo.get("questions_answers") or []
    h2s = aeo.get("structured_sections") or []
    entities = aeo.get("key_entities") or []
    keywords = seo.get("keywords") or []
    score = seo.get("score") or {}
    inject_ok = bool(inject.get("ok"))
    inject_skip = bool(inject.get("skipped"))
    arkiphere = connection.get("arkiphere") or {}
    pending = t(loc, "tree.pending")

    job = [
        _node(
            t(loc, "tree.order"),
            status="done" if order and order != "—" else "pending",
            icon="order",
            children=[
                _node(t(loc, "tree.orderName"), str(order), "done" if order and order != "—" else "pending"),
                _node(t(loc, "tree.site"), _host(site) or site or "—", "done" if site else "pending"),
                _node(t(loc, "tree.date"), _when(payload.get("generated_at")), "info"),
            ],
        ),
        _node(
            t(loc, "tree.connection"),
            platform_label,
            status=_status(bool(connection.get("connected"))),
            icon="plug",
            children=[
                _node(t(loc, "tree.platform"), platform_label, _status(bool(platform))),
                _node(
                    t(loc, "tree.status"),
                    t(loc, "tree.connected") if connection.get("connected") else pending,
                    _status(bool(connection.get("connected"))),
                ),
                _node(t(loc, "tree.user"), connection.get("username") or "—", "info") if platform == "odoo" else _node(
                    t(loc, "tree.access"),
                    t(loc, "tree.accessSaved") if connection.get("connected") else t(loc, "tree.accessMissing"),
                    _status(bool(connection.get("connected"))),
                ),
                _node(
                    t(loc, "tree.googleProfile"),
                    t(loc, "tree.googleProfileOn") if google_connected else t(loc, "tree.googleProfileOff"),
                    "done" if google_connected else "pending",
                ),
                _node(
                    t(loc, "tree.searchConsole"),
                    t(loc, "tree.searchConsoleOn") if google_connected else t(loc, "tree.searchConsoleOff"),
                    "done" if google_connected else "info",
                ),
                _node(
                    t(loc, "tree.arkLine"),
                    t(loc, "tree.arkVisible") if arkiphere.get("ok") else (arkiphere.get("message") or pending),
                    "done" if arkiphere.get("ok") else "info",
                ),
            ],
        ),
        _node(
            t(loc, "tree.googleAnalysis"),
            t(loc, "tree.googleAnalysisValue"),
            status=_status(bool(google.get("step_complete"))),
            icon="search",
            children=_gap_children(google, google_connected, loc)
            + [
                _node(
                    t(loc, "tree.competitors"),
                    t(loc, "tree.competitorsCopy"),
                    "done" if google.get("step_complete") else "info",
                ),
                _node(
                    t(loc, "tree.demand"),
                    t(loc, "tree.demandCopy"),
                    "done" if google.get("step_complete") else "info",
                ),
                _node(
                    t(loc, "tree.sendGoogle"),
                    t(loc, "tree.sendGoogleCopy"),
                    "info",
                ),
            ],
        ),
        _node(
            t(loc, "tree.aeo"),
            aeo.get("suggested_title") or t(loc, "progress.aeoDetail"),
            status=_status(bool(aeo)),
            icon="chat",
            children=[
                _node(t(loc, "tree.title"), aeo.get("suggested_title") or pending, _status(bool(aeo.get("suggested_title")))),
                _node(t(loc, "tree.summary"), aeo.get("summary") or pending, _status(bool(aeo.get("summary")))),
                _node(t(loc, "tree.entities"), ", ".join(str(e) for e in entities[:10]) if entities else pending, _status(bool(entities))),
                _node(
                    f"{t(loc, 'tree.faq')} ({len(faqs)})",
                    status=_status(bool(faqs)),
                    children=[
                        _node(qa.get("question") or t(loc, "tree.question", n=i + 1), qa.get("answer"), "done")
                        for i, qa in enumerate(faqs)
                    ]
                    if faqs
                    else [_node(t(loc, "tree.faq"), t(loc, "tree.faqEmpty"), "pending")],
                ),
                _node(
                    f"{t(loc, 'tree.sections')} ({len(h2s)})",
                    status=_status(bool(h2s)),
                    children=[_node(heading_label(h), status="done") for h in h2s if heading_label(h)]
                    if h2s
                    else [_node(t(loc, "tree.sections"), t(loc, "tree.structureEmpty"), "pending")],
                ),
            ],
        ),
        _node(
            t(loc, "tree.seo"),
            seo.get("title") or t(loc, "progress.seoDetail"),
            status=_status(bool(seo)),
            icon="tag",
            children=[
                _node(t(loc, "tree.seoTitle"), seo.get("title") or pending, _status(bool(seo.get("title")))),
                _node(t(loc, "tree.seoMeta"), seo.get("meta_description") or pending, _status(bool(seo.get("meta_description")))),
                _node(t(loc, "tree.keywords"), ", ".join(str(k) for k in keywords[:12]) if keywords else pending, _status(bool(keywords))),
                _node(t(loc, "tree.canonical"), seo.get("canonical") or site or "—", "info"),
                _node(
                    t(loc, "tree.score"),
                    f"{score.get('overall_score', '—')} / {score.get('max_score', '—')} · {score.get('grade', '—')}"
                    if score
                    else pending,
                    _status(bool(score)),
                ),
            ],
        ),
        _node(
            t(loc, "tree.publish"),
            t(loc, "tree.published") if inject_ok else (t(loc, "tree.skipped") if inject_skip else t(loc, "tree.notPublished")),
            status="done" if inject_ok else ("info" if inject_skip else ("warn" if inject else "pending")),
            icon="upload",
            children=[
                _node(
                    t(loc, "tree.result"),
                    inject.get("customer_message") or inject.get("message") or t(loc, "tree.notPublished"),
                    "done" if inject_ok else ("warn" if inject else "pending"),
                ),
                _node(
                    t(loc, "tree.wrote"),
                    t(loc, "tree.wroteSeo") if inject else t(loc, "tree.wroteNone"),
                    "info" if inject else "pending",
                ),
            ],
        ),
        _node(
            t(loc, "tree.scope"),
            t(loc, "tree.scopeHint"),
            status="info",
            icon="info",
            children=[
                _node(
                    t(loc, "tree.connection"),
                    t(loc, "tree.scopeConnectOn") if connection.get("connected") else t(loc, "tree.scopeConnectOff"),
                    _status(bool(connection.get("connected"))),
                ),
                _node(
                    t(loc, "tree.googleProfile"),
                    t(loc, "tree.googleProfileOn") if google_connected else t(loc, "tree.googleProfileOff"),
                    "done" if google_connected else "pending",
                ),
                _node(
                    t(loc, "tree.googleAnalysis"),
                    t(loc, "tree.scopeGoogleOn") if google.get("step_complete") else t(loc, "tree.scopeGoogleOff"),
                    _status(bool(google.get("step_complete"))),
                ),
                _node(
                    t(loc, "tree.aeo"),
                    t(loc, "tree.scopeAeoOn") if aeo else t(loc, "tree.scopeAeoOff"),
                    _status(bool(aeo)),
                ),
                _node(
                    t(loc, "tree.seo"),
                    t(loc, "tree.scopeSeoOn") if seo else t(loc, "tree.scopeSeoOff"),
                    _status(bool(seo)),
                ),
                _node(
                    t(loc, "tree.publish"),
                    inject.get("customer_message") or inject.get("message") or t(loc, "tree.notPublished"),
                    "done" if inject_ok else ("warn" if inject else "pending"),
                ),
                _node(
                    t(loc, "tree.sendGoogle"),
                    t(loc, "tree.scopeIndex"),
                    "info",
                ),
            ],
        ),
    ]
    return [node for node in job if node]


def build_summary(payload: Dict[str, Any], progress: Dict[str, Any]) -> str:
    connection = payload.get("connection") or {}
    google = payload.get("google") or {}
    pack = payload.get("pack") or {}
    inject = payload.get("inject") or {}
    aeo = pack.get("aeo") or {}
    seo = pack.get("seo") or {}
    loc = locale_of(payload.get("locale"))
    platform = PLATFORM_LABELS.get((payload.get("platform") or connection.get("platform") or "").lower(), "Odoo")
    site = _host(payload.get("site_url") or connection.get("url")) or payload.get("site_url") or "—"
    order = payload.get("sale_order_name") or connection.get("sale_order_name") or "—"
    gaps = google.get("gaps") or []
    passed = 0
    for gap in gaps:
        if gap.get("virtual_passed") or gap.get("passed"):
            passed += 1
    faq_n = len((aeo.get("questions_answers") or []))
    score = (seo.get("score") or {}).get("overall_score")
    parts = [t(loc, "summary.lead", order=order, site=site)]
    if connection.get("connected"):
        parts.append(t(loc, "summary.connectOn", platform=platform))
    else:
        parts.append(t(loc, "summary.connectOff"))
    if google.get("step_complete"):
        parts.append(t(loc, "summary.googleOn", passed=passed, total=len(gaps) or passed))
    else:
        parts.append(t(loc, "summary.googleOff"))
    if aeo:
        parts.append(t(loc, "summary.aeoOn", faq=faq_n))
    else:
        parts.append(t(loc, "summary.aeoOff"))
    if seo:
        parts.append(t(loc, "summary.seoOn", score=score if score is not None else "—"))
    else:
        parts.append(t(loc, "summary.seoOff"))
    if inject.get("ok"):
        parts.append(t(loc, "summary.publishOn"))
    elif inject.get("skipped"):
        parts.append(t(loc, "summary.publishSkip"))
    else:
        parts.append(t(loc, "summary.publishOff"))
    parts.append(f"{progress.get('percent', 0)}%.")
    return " ".join(parts)


def sanitize_payload(payload: Optional[Dict[str, Any]], bound: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    raw = _strip_secrets(payload or {})
    if not isinstance(raw, dict):
        raw = {}
    bound = bound or {}
    site = bound.get("bound_site_url") or raw.get("site_url") or ""
    pack = raw.get("pack") or {}
    if isinstance(pack, dict) and pack.get("content_draft"):
        pack = dict(pack)
        pack["content_draft"] = _clip(pack.get("content_draft"), 8000)
        raw["pack"] = pack
    google = raw.get("google") or {}
    if isinstance(google, dict):
        google = dict(google)
        google.pop("auth", None)
        google.pop("token", None)
        raw["google"] = google
    raw["site_url"] = site
    raw["host"] = bound.get("bound_host") or _host(site)
    raw["sale_order_name"] = bound.get("sale_order_name") or raw.get("sale_order_name")
    raw["generated_at"] = raw.get("generated_at") or _now()
    raw["license_tail"] = (bound.get("key") or "")[-4:]
    raw["locale"] = locale_of(raw.get("locale"))
    return raw


def build_dossier(payload: Optional[Dict[str, Any]], bound: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    clean = sanitize_payload(payload, bound)
    progress = build_progress(clean)
    tree = build_tree(clean)
    return {
        "generated_at": clean.get("generated_at"),
        "sale_order_name": clean.get("sale_order_name") or t(clean.get("locale"), "tree.order"),
        "site_url": clean.get("site_url") or "",
        "host": clean.get("host") or _host(clean.get("site_url")),
        "platform": clean.get("platform") or (clean.get("connection") or {}).get("platform"),
        "progress": progress,
        "summary": build_summary(clean, progress),
        "tree": tree,
        "payload": clean,
        "locale": clean.get("locale") or "es",
    }
