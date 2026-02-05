from fastapi import APIRouter
from app.schemas import KeywordsRequest, KeywordsResponse
from app.services.keywords_service import extract_keywords

router = APIRouter()


@router.post("/extract", response_model=KeywordsResponse)
async def extract(req: KeywordsRequest):
    return extract_keywords(req)
