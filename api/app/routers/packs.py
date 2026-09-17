from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.chat_service import check_ollama_health
from app.services.pack_service import generate_pack

router = APIRouter()


class PackRequest(BaseModel):
    topic: str = Field(..., min_length=1, max_length=200)
    url: Optional[str] = None
    business_name: Optional[str] = None
    context: Optional[str] = None
    locale: Optional[str] = "en"


@router.get("/health")
async def packs_health():
    return await check_ollama_health()


@router.post("/generate")
async def packs_generate(req: PackRequest):
    return await generate_pack(
        topic=req.topic,
        url=req.url,
        business_name=req.business_name,
        context=req.context,
        locale=req.locale or "en",
    )
