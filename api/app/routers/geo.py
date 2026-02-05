"""
GEO (Generative Engine Optimization) Router

Endpoints for optimizing content for AI-powered generative search engines
like ChatGPT, Perplexity, Google AI Overviews, and Microsoft Copilot.
"""

from fastapi import APIRouter
from app.schemas import (
    GEOAnalyzeRequest, GEOAnalyzeResponse,
    GEOOptimizeRequest, GEOOptimizeResponse,
    GEOCitationRequest, GEOCitationResponse,
)
from app.services.geo_service import (
    analyze_geo_content,
    generate_geo_suggestions,
    enhance_citations,
)

router = APIRouter(prefix="/api/geo", tags=["GEO (Generative Engine Optimization)"])


@router.post("/analyze", response_model=GEOAnalyzeResponse)
def analyze(req: GEOAnalyzeRequest):
    """
    Analyze content for Generative Engine Optimization.
    
    Evaluates content for factors that improve visibility in AI-generated
    responses: statistics, citations, authoritative language, quotable
    definitions, structure, Q&A format, and fluency.
    
    Returns a GEO score (0-110), grade (A-F), per-check results, and
    actionable recommendations.
    """
    return analyze_geo_content(req)


@router.post("/optimize", response_model=GEOOptimizeResponse)
def optimize(req: GEOOptimizeRequest):
    """
    Generate GEO optimization suggestions for a topic.
    
    Returns:
    - Suggested quotable definition
    - Q&A pairs matching common AI queries
    - Citation and statistic templates
    - Recommended content structure
    - GEO best practice tips
    """
    return generate_geo_suggestions(req)


@router.post("/citations", response_model=GEOCitationResponse)
def citations(req: GEOCitationRequest):
    """
    Analyze content and suggest citation enhancements.
    
    Identifies sentences that make claims without citations and suggests
    how to add authoritative references. Also finds opportunities to
    add specific statistics to vague statements.
    """
    return enhance_citations(req)
