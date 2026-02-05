import re
from collections import Counter
from app.schemas import KeywordsRequest, KeywordsResponse, KeywordItem

try:
    from app.services.nlp_service import extract_keywords_rake
    RAKE_AVAILABLE = True
except Exception:
    RAKE_AVAILABLE = False

STOP_WORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "as", "is", "was", "are", "were", "been",
    "be", "have", "has", "had", "do", "does", "did", "will", "would",
    "could", "should", "may", "might", "must", "shall", "can", "need",
    "this", "that", "these", "those", "it", "its", "they", "them",
    "we", "our", "you", "your", "he", "she", "his", "her", "i", "my",
}


def _tokenize(text: str) -> list[str]:
    text = text.lower()
    words = re.findall(r"\b[a-z0-9]{2,}\b", text)
    return [w for w in words if w not in STOP_WORDS]


def extract_keywords(req: KeywordsRequest) -> KeywordsResponse:
    use_rake = getattr(req, "use_rake", False) and RAKE_AVAILABLE
    if use_rake:
        rake_phrases = extract_keywords_rake(req.text, req.max_keywords)
        words = _tokenize(req.text)
        word_count = len(words) or len(req.text.split())
        keywords = [
            KeywordItem(keyword=p, count=0, density=0)
            for p, _ in rake_phrases
        ]
    else:
        words = _tokenize(req.text)
        word_count = len(words)
        if not words:
            return KeywordsResponse(
                keywords=[],
                word_count=len(req.text.split()),
                suggestions=[],
            )
        counts = Counter(words).most_common(req.max_keywords)
        keywords = [
            KeywordItem(
                keyword=k,
                count=c,
                density=round(100 * c / word_count, 2),
            )
            for k, c in counts
        ]
    
    suggestions = []
    if word_count < 300:
        suggestions.append("Consider adding more content (300+ words) for better SEO.")
    if len(keywords) < 3:
        suggestions.append("Use a clearer focus on 2–3 main topics to improve keyword relevance.")
    suggestions.append("Use primary keywords in the first 100 words and in headings.")
    
    return KeywordsResponse(
        keywords=keywords,
        word_count=word_count,
        suggestions=suggestions,
    )
