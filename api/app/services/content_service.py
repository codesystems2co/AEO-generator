import re
from app.schemas import ContentAnalysisRequest, ContentAnalysisResponse
from app.services.nlp_service import get_readability


def analyze_content(req: ContentAnalysisRequest) -> ContentAnalysisResponse:
    text = req.text.strip()
    words = text.split()
    word_count = len(words)
    sentences = re.split(r"[.!?]+", text)
    sentences = [s.strip() for s in sentences if s.strip()]
    sentence_count = len(sentences)
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    paragraph_count = len(paragraphs)
    
    reading_time = word_count / 200.0 if word_count else 0
    
    headings = []
    for line in text.split("\n"):
        line = line.strip()
        if line.startswith("#") or (len(line) < 100 and line.endswith(":") and line[0].isupper()):
            headings.append(line.lstrip("#").strip())
    
    keyword_density = None
    if req.target_keyword and req.target_keyword.strip():
        kw = req.target_keyword.lower().strip()
        count = sum(1 for w in words if w.lower() == kw or kw in w.lower())
        keyword_density = round(100 * count / word_count, 2) if word_count else 0
    
    recommendations = []
    if word_count < 300:
        recommendations.append("Add more content: aim for at least 300 words for better SEO.")
    if sentence_count and word_count / sentence_count > 25:
        recommendations.append("Use shorter sentences for readability (aim for ~15–20 words).")
    if paragraph_count and word_count / paragraph_count > 150:
        recommendations.append("Break long paragraphs into 3–5 sentences for scannability.")
    if not headings:
        recommendations.append("Add clear headings (H2/H3) to structure content and help AEO.")
    if keyword_density is not None and keyword_density < 0.5:
        recommendations.append(f"Increase use of target keyword '{req.target_keyword}' naturally.")
    if keyword_density is not None and keyword_density > 3:
        recommendations.append("Reduce keyword density to avoid stuffing; keep under ~2%.")
    
    readability = get_readability(text)
    
    return ContentAnalysisResponse(
        word_count=word_count,
        reading_time_minutes=round(reading_time, 1),
        sentence_count=sentence_count,
        paragraph_count=paragraph_count,
        keyword_density=keyword_density,
        headings=headings[:20],
        recommendations=recommendations,
        readability=readability,
    )
