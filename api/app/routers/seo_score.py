from fastapi import APIRouter
from app.schemas import SEOScoreRequest, SEOScoreResponse
from app.services.seo_score_service import calculate_seo_score

router = APIRouter()


@router.post("/calculate", response_model=SEOScoreResponse)
async def calculate(req: SEOScoreRequest):
    return calculate_seo_score(req)
