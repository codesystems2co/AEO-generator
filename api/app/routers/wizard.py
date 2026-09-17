from typing import Any, Dict, Optional

from fastapi import APIRouter, Header
from pydantic import BaseModel, Field

from app.services.chat_service import check_ollama_health
from app.services.connection_store import record_apply, secrets_for
from app.services.core_client import probe_core
from app.services.google_search_service import status as google_status
from app.services.gsc_autofix_service import autofix
from app.services.inject_service import inject_and_verify
from app.services.pack_service import generate_pack
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
        "steps": ["connect", "google", "aeo", "seo", "inject"],
    }


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
    )
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
    )
    record_apply(_license(x_aeo_license, req), inject)
    return {
        "ok": bool(gsc.get("step_complete") and pack.get("ok")),
        "google": gsc,
        "pack": pack,
        "inject": inject,
        "site_url": site,
    }
