from fastapi import APIRouter
from app.schemas import (
    NLPKeywordsRequest,
    ReadabilityRequest,
    ReadabilityResponse,
)
from app.services.nlp_service import extract_keywords_rake, get_readability

router = APIRouter()


@router.post("/keywords")
async def nlp_keywords(req: NLPKeywordsRequest):
    """Extract keywords using RAKE (NLP) or frequency-based method."""
    if req.method == "rake":
        phrases = extract_keywords_rake(req.text, req.max_keywords)
        return {
            "method": "rake",
            "keywords": [{"phrase": p, "score": s} for p, s in phrases],
            "word_count": len(req.text.split()),
        }
    return {"method": "frequency", "message": "Use /api/keywords/extract for frequency-based extraction."}


@router.post("/readability", response_model=ReadabilityResponse)
async def readability(req: ReadabilityRequest):
    """Compute readability metrics (Flesch, SMOG, ARI)."""
    data = get_readability(req.text)
    if not data:
        return ReadabilityResponse(
            flesch_reading_ease=0,
            flesch_kincaid_grade=0,
            smog_index=0,
            automated_readability_index=0,
            sentence_count=0,
            word_count=0,
            interpretation="Readability not available (install textstat or provide longer text).",
        )
    return ReadabilityResponse(**data)
