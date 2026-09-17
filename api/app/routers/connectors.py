from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.core_client import PLATFORMS, probe_core, verify_seo, write_seo

router = APIRouter()


class ConnectorBody(BaseModel):
    platform: str = Field(..., description="odoo | prestashop | woocommerce")
    connection: Dict[str, Any] = Field(default_factory=dict)
    seo: Dict[str, Any] = Field(default_factory=dict)
    target: Optional[str] = None


@router.get("/health")
async def connectors_health():
    return await probe_core()


@router.get("/platforms")
async def connectors_platforms():
    return {"platforms": list(PLATFORMS), "actions": ["write-seo", "verify"]}


@router.post("/write")
async def connectors_write(body: ConnectorBody):
    platform = body.platform.strip().lower()
    if platform not in PLATFORMS:
        raise HTTPException(status_code=400, detail=f"Unsupported platform. Use: {', '.join(PLATFORMS)}")
    payload = {
        "connection": body.connection,
        "seo": body.seo,
        "target": body.target,
    }
    result = await write_seo(platform, payload)
    if not result.get("forwarded") and not result.get("ok"):
        health = await probe_core()
        result["core"] = health
    return result


@router.post("/verify")
async def connectors_verify(body: ConnectorBody):
    platform = body.platform.strip().lower()
    if platform not in PLATFORMS:
        raise HTTPException(status_code=400, detail=f"Unsupported platform. Use: {', '.join(PLATFORMS)}")
    payload = {
        "connection": body.connection,
        "seo": body.seo,
        "target": body.target,
    }
    result = await verify_seo(platform, payload)
    if not result.get("forwarded") and not result.get("ok"):
        health = await probe_core()
        result["core"] = health
    return result
