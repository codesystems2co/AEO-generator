from typing import Any, Dict, Optional

from fastapi import APIRouter, Header
from fastapi.responses import Response
from pydantic import BaseModel, Field

from app.services.chat_service import check_ollama_health
from app.services.connection_store import get_job, record_apply, record_job, remember_database, secrets_for
from app.services.core_client import probe_core
from app.services.google_search_service import status as google_status
from app.services.gsc_autofix_service import autofix
from app.services.inject_service import inject_and_verify
from app.services.job_changelog import compare_cycles, fingerprint
from app.services.job_memory import build_reading
from app.services.job_report_service import build_dossier
from app.services.pack_service import generate_pack
from app.services.pdf_report_service import render_job_pdf
from app.services.site_guard import bind_license_site, extract_license

router = APIRouter()


class WizardRunRequest(BaseModel):
    site_url: str = Field(..., min_length=3)
    topic: str = Field(..., min_length=1)
    mode: Optional[str] = None
    business_name: Optional[str] = None
    context: Optional[str] = None
    locale: Optional[str] = "es"
    license: Optional[str] = None
    key: Optional[str] = None


class AutofixRequest(BaseModel):
    site_url: str = Field(..., min_length=3)
    mode: Optional[str] = "oauth"
    topic: Optional[str] = None
    context: Optional[str] = None
    locale: Optional[str] = "es"
    license: Optional[str] = None
    key: Optional[str] = None


class InjectRequest(BaseModel):
    seo: Dict[str, Any] = Field(default_factory=dict)
    connections: Optional[Dict[str, Any]] = None
    target: Optional[str] = None
    site_url: Optional[str] = None
    license: Optional[str] = None
    key: Optional[str] = None
    locale: Optional[str] = None


class JobReportRequest(BaseModel):
    site_url: Optional[str] = None
    license: Optional[str] = None
    key: Optional[str] = None
    sale_order_name: Optional[str] = None
    platform: Optional[str] = None
    connect_done: Optional[bool] = None
    google_connected: Optional[bool] = None
    locale: Optional[str] = None
    connection: Optional[Dict[str, Any]] = None
    google: Optional[Dict[str, Any]] = None
    pack: Optional[Dict[str, Any]] = None
    inject: Optional[Dict[str, Any]] = None
    aeo: Optional[Dict[str, Any]] = None
    seo: Optional[Dict[str, Any]] = None


def _license(header: Optional[str], body) -> str:
    return extract_license(header, getattr(body, "license", None), getattr(body, "key", None))


@router.get("/status")
async def wizard_status():
    ollama = await check_ollama_health()
    core = await probe_core()
    google = google_status()
    return {
        "google": google,
        "ollama": ollama,
        "core": core,
        "steps": ["connect", "google", "aeo", "seo", "inject", "report"],
    }


async def _dossier_from_request(
    req: JobReportRequest,
    x_aeo_license: Optional[str],
) -> Dict[str, Any]:
    bound = bind_license_site(_license(x_aeo_license, req), req.site_url)
    payload = req.model_dump()
    has_live = any(
        payload.get(key) not in (None, {}, [])
        for key in ("connection", "google", "pack", "inject", "aeo", "seo")
    )
    stored = get_job(bound.get("key") or _license(x_aeo_license, req)) or {}
    if not has_live:
        prev = stored.get("payload") if isinstance(stored, dict) else None
        if isinstance(prev, dict):
            payload = prev
    cycles = stored.get("cycles") if isinstance(stored, dict) else None
    previous_fp = None
    if isinstance(cycles, list) and cycles:
        last = cycles[-1]
        if isinstance(last, dict) and isinstance(last.get("fingerprint"), dict):
            previous_fp = last.get("fingerprint")
    dossier = build_dossier(payload, bound)
    current_fp = fingerprint(dossier.get("payload") or payload)
    dossier["fingerprint"] = current_fp
    dossier["changelog"] = compare_cycles(previous_fp, current_fp, dossier.get("locale"))
    dossier["reading"] = await build_reading(
        stored.get("archives") if isinstance(stored, dict) else None,
        cycles if isinstance(cycles, list) else None,
        stored.get("readings") if isinstance(stored, dict) else None,
        dossier,
    )
    record_job(bound.get("key") or _license(x_aeo_license, req), dossier)
    return dossier


@router.post("/google/autofix")
async def wizard_google_autofix(
    req: AutofixRequest,
    x_aeo_license: Optional[str] = Header(default=None, alias="X-AEO-License"),
):
    bound = bind_license_site(_license(x_aeo_license, req), req.site_url)
    return await autofix(
        site_url=bound["bound_site_url"],
        mode=req.mode,
        topic=req.topic,
        context=req.context,
        locale=req.locale or "es",
    )


@router.post("/inject-verify")
async def wizard_inject_verify(
    req: InjectRequest,
    x_aeo_license: Optional[str] = Header(default=None, alias="X-AEO-License"),
):
    bound = bind_license_site(_license(x_aeo_license, req), req.site_url)
    stored = secrets_for(bound.get("key") or _license(x_aeo_license, req))
    connections = req.connections or {}
    platform = (stored.get("platform") or "odoo").strip().lower()
    if stored.get("url") and platform not in connections:
        connections[platform] = stored
    result = await inject_and_verify(
        seo=req.seo or {},
        connections=connections,
        target=req.target or bound["bound_site_url"],
        locale=req.locale,
    )
    direct = result.get("direct") if isinstance(result.get("direct"), dict) else {}
    if direct.get("database"):
        remember_database(bound.get("key") or _license(x_aeo_license, req), "odoo", direct.get("database"))
    record_apply(_license(x_aeo_license, req), result)
    return result


@router.post("/run")
async def wizard_run(
    req: WizardRunRequest,
    x_aeo_license: Optional[str] = Header(default=None, alias="X-AEO-License"),
):
    bound = bind_license_site(_license(x_aeo_license, req), req.site_url)
    site = bound["bound_site_url"]
    gsc = await autofix(
        site_url=site,
        mode=req.mode,
        topic=req.topic or req.business_name,
        context=req.context,
        locale=req.locale or "es",
    )
    pack = await generate_pack(
        topic=req.topic,
        url=site,
        business_name=req.business_name,
        context=req.context,
        locale=req.locale or "es",
    )
    stored = secrets_for(_license(x_aeo_license, req))
    connections = {}
    platform = (stored.get("platform") or "").strip().lower()
    if stored.get("url") and platform:
        connections[platform] = stored
    inject = await inject_and_verify(
        seo={
            "title": (pack.get("seo") or {}).get("title"),
            "meta_description": (pack.get("seo") or {}).get("meta_description"),
            "keywords": (pack.get("seo") or {}).get("keywords"),
            "canonical": site,
        },
        connections=connections or None,
        target=site,
        locale=req.locale or "es",
    )
    direct = inject.get("direct") if isinstance(inject.get("direct"), dict) else {}
    if direct.get("database"):
        remember_database(_license(x_aeo_license, req), "odoo", direct.get("database"))
    record_apply(_license(x_aeo_license, req), inject)
    return {
        "ok": bool(gsc.get("step_complete") and pack.get("ok")),
        "google": gsc,
        "pack": pack,
        "inject": inject,
        "site_url": site,
    }


@router.post("/job")
async def wizard_job(
    req: JobReportRequest,
    x_aeo_license: Optional[str] = Header(default=None, alias="X-AEO-License"),
):
    dossier = await _dossier_from_request(req, x_aeo_license)
    reading = dossier.get("reading") if isinstance(dossier.get("reading"), dict) else {}
    return {
        "ok": True,
        "generated_at": dossier.get("generated_at"),
        "sale_order_name": dossier.get("sale_order_name"),
        "site_url": dossier.get("site_url"),
        "host": dossier.get("host"),
        "progress": dossier.get("progress"),
        "summary": dossier.get("summary"),
        "tree": dossier.get("tree"),
        "changelog": dossier.get("changelog") or {},
        "reading": {key: reading.get(key) for key in ("ready", "source", "summary")},
    }


@router.post("/report.pdf")
async def wizard_report_pdf(
    req: JobReportRequest,
    x_aeo_license: Optional[str] = Header(default=None, alias="X-AEO-License"),
):
    from app.services.i18n_copy import locale_of

    dossier = await _dossier_from_request(req, x_aeo_license)
    pdf = render_job_pdf(dossier)
    loc = locale_of(dossier.get("locale"))
    order = (dossier.get("sale_order_name") or ("order" if loc == "en" else "pedido")).replace(" ", "")
    host = (dossier.get("host") or ("site" if loc == "en" else "sitio")).replace(" ", "")
    prefix = "report" if loc == "en" else "informe"
    filename = f"{prefix}-optimizator-{order}-{host}.pdf"
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Type": "application/pdf",
        },
    )
