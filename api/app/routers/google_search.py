from typing import Optional

from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field

from app.config import settings
from app.services import google_search_service as gsc
from app.services.site_guard import bind_license_site, extract_license

router = APIRouter()


class ReadinessRequest(BaseModel):
    site_url: str = Field(..., min_length=3)
    mode: Optional[str] = Field(default=None, description="oauth | service_account")
    license: Optional[str] = None
    key: Optional[str] = None


class ServiceAccountBody(BaseModel):
    json_key: str = Field(..., min_length=20)


@router.get("/status")
async def google_status():
    return gsc.status()


@router.post("/readiness")
async def google_readiness(
    req: ReadinessRequest,
    x_aeo_license: Optional[str] = Header(default=None, alias="X-AEO-License"),
):
    bound = bind_license_site(extract_license(x_aeo_license, req.license, req.key), req.site_url)
    return await gsc.readiness(bound["bound_site_url"], mode=req.mode)


@router.post("/oauth/start")
async def oauth_start():
    data = gsc.start_oauth()
    if not data.get("ok"):
        raise HTTPException(status_code=400, detail=data.get("error") or "OAuth not configured")
    return data


@router.get("/oauth/callback")
async def oauth_callback(code: Optional[str] = None, state: Optional[str] = None, error: Optional[str] = None):
    frontend = (settings.FRONTEND_PUBLIC_URL or "http://2.28.106.22:9012").rstrip("/")
    if error:
        return RedirectResponse(f"{frontend}/?gsc=error&reason={error}")
    result = await gsc.finish_oauth(code or "", state or "")
    if not result.get("ok"):
        return RedirectResponse(f"{frontend}/?gsc=error")
    return RedirectResponse(f"{frontend}/?gsc=connected")


@router.get("/sites")
async def google_sites():
    return await gsc.gsc_sites()


@router.post("/sa/session")
async def google_sa_session(body: ServiceAccountBody):
    return gsc.set_session_sa(body.json_key)
