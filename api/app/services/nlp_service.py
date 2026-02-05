"""NLP services: RAKE keyword extraction and readability metrics."""
import re
from typing import List, Optional

try:
    from rake_nltk import Rake
    RAKE_AVAILABLE = True
except ImportError:
    RAKE_AVAILABLE = False

try:
    import textstat
    TEXTSTAT_AVAILABLE = True
except ImportError:
    TEXTSTAT_AVAILABLE = False


def extract_keywords_rake(text: str, max_keywords: int = 15) -> List[tuple]:
    """Extract keywords using RAKE (Rapid Automatic Keyword Extraction)."""
    if not RAKE_AVAILABLE:
        return []
    text_clean = re.sub(r"\s+", " ", text.strip())
    if len(text_clean) < 20:
        return []
    r = Rake(min_length=2, max_length=4)
    r.extract_keywords_from_text(text_clean)
    phrases = r.get_ranked_phrases()
    return [(p, 0) for p in phrases[:max_keywords]]


def get_readability(text: str) -> Optional[dict]:
    """Compute readability metrics using textstat (Flesch, SMOG, ARI, etc.)."""
    if not TEXTSTAT_AVAILABLE or not text or len(text.strip()) < 20:
        return None
    try:
        flesch = textstat.flesch_reading_ease(text)
        fk_grade = textstat.flesch_kincaid_grade(text)
        smog = textstat.smog_index(text)
        ari = textstat.automated_readability_index(text)
        sent_count = textstat.sentence_count(text)
        word_count = textstat.lexicon_count(text)
        if flesch >= 60:
            interp = "Easy to read (suitable for general audience)."
        elif flesch >= 30:
            interp = "Moderate difficulty (consider simplifying for broader reach)."
        else:
            interp = "Difficult; consider shorter sentences and simpler words for SEO."
        return {
            "flesch_reading_ease": round(flesch, 2),
            "flesch_kincaid_grade": round(fk_grade, 2),
            "smog_index": round(smog, 2),
            "automated_readability_index": round(ari, 2),
            "sentence_count": sent_count,
            "word_count": word_count,
            "interpretation": interp,
        }
    except Exception:
        return None
