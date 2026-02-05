from fastapi import APIRouter
from app.schemas import (
    ExternalSEOMozRequest,
    ExternalSEOMozResponse,
    ExternalSEOSemrushRequest,
    ExternalSEOSemrushResponse,
)
from app.services.external_seo_service import fetch_moz_metrics, fetch_semrush_overview

router = APIRouter()


@router.post("/moz", response_model=ExternalSEOMozResponse)
async def moz_metrics(req: ExternalSEOMozRequest):
    """Fetch Domain Authority, Page Authority from Moz (requires MOZ_ACCESS_ID, MOZ_SECRET_KEY)."""
    return fetch_moz_metrics(req.url)


@router.post("/semrush", response_model=ExternalSEOSemrushResponse)
async def semrush_overview(req: ExternalSEOSemrushRequest):
    """Fetch domain rank from SEMrush (requires SEMRUSH_API_KEY)."""
    return fetch_semrush_overview(req.domain, req.database)
