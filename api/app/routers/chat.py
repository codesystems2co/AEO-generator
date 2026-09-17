from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.chat_service import (
    chat as chat_service,
    check_ollama_health,
    check_airllm_health,
)
from app.config import settings

router = APIRouter()


class ChatMessage(BaseModel):
    role: str = Field(..., description="user | assistant | system")
    content: str = Field(..., min_length=1)


class ChatRequest(BaseModel):
    messages: List[ChatMessage] = Field(..., min_length=1)
    business_name: Optional[str] = None
    url: Optional[str] = None
    locale: Optional[str] = "es"


class ChatResponse(BaseModel):
    reply: str
    suggestions: Optional[Dict[str, Any]] = None
    backend: Optional[str] = None


@router.get("/health")
async def health():
    air = await check_airllm_health() if getattr(settings, "AIRLLM_ENABLED", False) else {"status": "disabled"}
    oll = await check_ollama_health()
    status = "ok" if (air.get("status") == "ok" or oll.get("status") == "ok") else "error"
    result = {"status": status, "airllm": air, "ollama": oll}
    if status != "ok":
        raise HTTPException(status_code=503, detail=result)
    return result


@router.post("/", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    msgs = [{"role": m.role, "content": m.content} for m in req.messages]
    try:
        result = await chat_service(
            messages=msgs,
            business_name=req.business_name,
            url=req.url,
            locale=req.locale or "es",
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Chat backend error: {str(e)[:200]}")
    return ChatResponse(
        reply=result.get("reply") or "",
        suggestions=result.get("suggestions"),
        backend=result.get("backend"),
    )
