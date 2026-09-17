from typing import Any, Dict, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.chat_service import check_ollama_health
from app.services.core_client import probe_core
from app.services.google_search_service import status as google_status
from app.services.gsc_autofix_service import autofix
from app.services.inject_service import inject_and_verify
from app.services.pack_service import generate_pack

router = APIRouter()


class WizardRunRequest(BaseModel):
    site_url: str = Field(..., min_length=3)
    topic: str = Field(..., min_length=1)
    mode: Optional[str] = None
    business_name: Optional[str] = None
    context: Optional[str] = None
    locale: Optional[str] = "es"


class AutofixRequest(BaseModel):
    site_url: str = Field(..., min_length=3)
    mode: Optional[str] = "oauth"
    topic: Optional[str] = None
    context: Optional[str] = None
    locale: Optional[str] = "es"


class InjectRequest(BaseModel):
    seo: Dict[str, Any] = Field(default_factory=dict)
    connections: Optional[Dict[str, Any]] = None
    target: Optional[str] = None


@router.get("/status")
async def wizard_status():
    ollama = await check_ollama_health()
    core = await probe_core()
    google = google_status()
    return {
        "google": google,
        "ollama": ollama,
        "core": core,
        "steps": ["shop", "google", "aeo", "seo", "inject"],
    }


@router.post("/google/autofix")
async def wizard_google_autofix(req: AutofixRequest):
    return await autofix(
        site_url=req.site_url,
        mode=req.mode,
        topic=req.topic,
        context=req.context,
        locale=req.locale or "es",
    )


@router.post("/inject-verify")
async def wizard_inject_verify(req: InjectRequest):
    return await inject_and_verify(
        seo=req.seo or {},
        connections=req.connections,
        target=req.target,
    )


@router.post("/run")
async def wizard_run(req: WizardRunRequest):
    gsc = await autofix(
        site_url=req.site_url,
        mode=req.mode,
        topic=req.topic or req.business_name,
        context=req.context,
        locale=req.locale or "es",
    )
    pack = await generate_pack(
        topic=req.topic,
        url=req.site_url,
        business_name=req.business_name,
        context=req.context,
        locale=req.locale or "es",
    )
    inject = await inject_and_verify(
        seo={
            "title": (pack.get("seo") or {}).get("title"),
            "meta_description": (pack.get("seo") or {}).get("meta_description"),
            "keywords": (pack.get("seo") or {}).get("keywords"),
            "canonical": req.site_url,
        }
    )
    return {
        "ok": bool(gsc.get("step_complete") and pack.get("ok")),
        "google": gsc,
        "pack": pack,
        "inject": inject,
    }
