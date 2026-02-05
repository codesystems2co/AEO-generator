from fastapi import APIRouter
from app.schemas import ContentAnalysisRequest, ContentAnalysisResponse
from app.services.content_service import analyze_content

router = APIRouter()


@router.post("/content", response_model=ContentAnalysisResponse)
async def analyze(req: ContentAnalysisRequest):
    return analyze_content(req)
