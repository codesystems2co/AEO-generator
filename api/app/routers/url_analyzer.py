from fastapi import APIRouter
from app.schemas import URLAnalyzeRequest, URLAnalyzeResponse
from app.services.url_analyzer_service import analyze_url

router = APIRouter()


@router.post("/analyze", response_model=URLAnalyzeResponse)
async def analyze_url_endpoint(req: URLAnalyzeRequest):
    """Fetch URL and extract meta tags, headings, and word count."""
    return analyze_url(req.url)
