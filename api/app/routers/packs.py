from typing import Optional

from typing import Optional

from fastapi import APIRouter, Header
from pydantic import BaseModel, Field

from app.services.chat_service import check_ollama_health
from app.services.pack_service import generate_pack
from app.services.site_guard import bind_license_site, extract_license

router = APIRouter()


class PackRequest(BaseModel):
    topic: str = Field(..., min_length=1, max_length=200)
    url: Optional[str] = None
    business_name: Optional[str] = None
    context: Optional[str] = None
    locale: Optional[str] = "en"
    license: Optional[str] = None
    key: Optional[str] = None


@router.get("/health")
async def packs_health():
    return await check_ollama_health()


@router.post("/generate")
async def packs_generate(
    req: PackRequest,
    x_aeo_license: Optional[str] = Header(default=None, alias="X-AEO-License"),
):
    bound = bind_license_site(extract_license(x_aeo_license, req.license, req.key), req.url)
    return await generate_pack(
        topic=req.topic,
        url=bound["bound_site_url"],
        business_name=req.business_name,
        context=req.context,
        locale=req.locale or "en",
    )
