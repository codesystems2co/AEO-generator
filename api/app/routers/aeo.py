from fastapi import APIRouter
from app.schemas import AEORequest, AEResponse
from app.services.aeo_service import generate_aeo_suggestions

router = APIRouter()


@router.post("/suggest", response_model=AEResponse)
async def suggest(req: AEORequest):
    return generate_aeo_suggestions(req)
