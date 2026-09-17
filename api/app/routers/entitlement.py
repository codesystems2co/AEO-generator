from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services import entitlement_service as entitlement

router = APIRouter()


class EntitlementCheck(BaseModel):
    github_login: Optional[str] = Field(default=None)


class EntitlementRegister(BaseModel):
    github_login: Optional[str] = None
    sale_order_name: str = Field(..., min_length=1)
    partner_name: Optional[str] = None
    source: Optional[str] = "arkiphere"


class EntitlementRevoke(BaseModel):
    github_login: Optional[str] = None
    sale_order_name: Optional[str] = None


class EntitlementConsume(BaseModel):
    key: Optional[str] = None
    github_login: Optional[str] = None


@router.get("/check")
async def entitlement_check(github_login: Optional[str] = None):
    return entitlement.check(github_login)


@router.post("/check")
async def entitlement_check_post(body: EntitlementCheck):
    return entitlement.check(body.github_login)


@router.post("/register")
async def entitlement_register(body: EntitlementRegister):
    return entitlement.register_confirmed(
        github_login=body.github_login,
        sale_order_name=body.sale_order_name,
        partner_name=body.partner_name,
        source=body.source or "arkiphere",
    )


@router.post("/revoke")
async def entitlement_revoke(body: EntitlementRevoke):
    return entitlement.revoke(body.github_login, body.sale_order_name)


@router.get("/consume")
async def entitlement_consume_get(key: Optional[str] = None, github_login: Optional[str] = None):
    return entitlement.consume(key, github_login)


@router.post("/consume")
async def entitlement_consume_post(body: EntitlementConsume):
    return entitlement.consume(body.key, body.github_login)
