from pydantic import BaseModel, Field
from typing import Optional, List


# Meta tags
class MetaTagsRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=120)
    description: str = Field(..., min_length=1, max_length=320)
    url: Optional[str] = None
    image_url: Optional[str] = None
    site_name: Optional[str] = None
    type: str = "website"


class MetaTagsResponse(BaseModel):
    title_tag: str
    meta_description: str
    og_tags: dict
    twitter_card: dict
    canonical: Optional[str] = None


# Keywords
class KeywordsRequest(BaseModel):
    text: str = Field(..., min_length=10)
    max_keywords: int = Field(default=10, ge=1, le=50)
    use_rake: bool = False  # Use NLP RAKE when True


class KeywordItem(BaseModel):
    keyword: str
    count: int
    density: float


class KeywordsResponse(BaseModel):
    keywords: List[KeywordItem]
    word_count: int
    suggestions: List[str]


# Content analysis
class ContentAnalysisRequest(BaseModel):
    text: str = Field(..., min_length=10)
    target_keyword: Optional[str] = None


class ContentAnalysisResponse(BaseModel):
    word_count: int
    reading_time_minutes: float
    sentence_count: int
    paragraph_count: int
    keyword_density: Optional[float] = None
    headings: List[str]
    recommendations: List[str]
    readability: Optional[dict] = None  # flesch_reading_ease, flesch_kincaid_grade, etc.


# AEO
class AEORequest(BaseModel):
    topic: str = Field(..., min_length=1)
    context: Optional[str] = None
    include_qa: bool = True
    include_entities: bool = True


class AEOQuestionAnswer(BaseModel):
    question: str
    answer: str


class AEResponse(BaseModel):
    suggested_title: str
    summary: str
    key_entities: List[str]
    questions_answers: List[AEOQuestionAnswer]
    structured_sections: List[str]
    tips: List[str]


# SEO score
class SEOScoreRequest(BaseModel):
    title: str = Field(..., max_length=120)
    meta_description: str = Field(..., max_length=320)
    content: str = Field(..., min_length=50)
    url: Optional[str] = None


class ScoreItem(BaseModel):
    name: str
    score: int
    max_score: int
    passed: bool
    message: str


class SEOScoreResponse(BaseModel):
    overall_score: int
    max_score: int
    grade: str
    checks: List[ScoreItem]
    recommendations: List[str]


# NLP
class NLPKeywordsRequest(BaseModel):
    text: str = Field(..., min_length=10)
    method: str = "rake"  # "rake" | "frequency"
    max_keywords: int = Field(default=15, ge=1, le=50)


class ReadabilityRequest(BaseModel):
    text: str = Field(..., min_length=20)


class ReadabilityResponse(BaseModel):
    flesch_reading_ease: float
    flesch_kincaid_grade: float
    smog_index: float
    automated_readability_index: float
    sentence_count: int
    word_count: int
    interpretation: str


# URL analyzer (external content)
class URLAnalyzeRequest(BaseModel):
    url: str = Field(..., min_length=10)


class URLAnalyzeResponse(BaseModel):
    url: str
    title: Optional[str] = None
    meta_description: Optional[str] = None
    og_title: Optional[str] = None
    og_description: Optional[str] = None
    h1_list: List[str]
    headings: List[str]
    word_count: int
    status_code: Optional[int] = None
    error: Optional[str] = None


# External SEO APIs (Moz, SEMrush)
class ExternalSEOMozRequest(BaseModel):
    url: str = Field(..., min_length=10)


class ExternalSEOMozResponse(BaseModel):
    url: str
    available: bool
    message: str
    domain_authority: Optional[float] = None
    page_authority: Optional[float] = None
    spam_score: Optional[float] = None


class ExternalSEOSemrushRequest(BaseModel):
    domain: str = Field(..., min_length=2)
    database: str = "us"


class ExternalSEOSemrushResponse(BaseModel):
    domain: str
    available: bool
    message: str
    rank: Optional[int] = None
    organic_traffic: Optional[int] = None
    organic_keywords: Optional[int] = None


# GEO (Generative Engine Optimization)
class GEOAnalyzeRequest(BaseModel):
    content: str = Field(..., min_length=50)


class GEOOptimizeRequest(BaseModel):
    topic: str = Field(..., min_length=2)
    context: Optional[str] = None


class GEOCitationRequest(BaseModel):
    content: str = Field(..., min_length=50)


class GEOCheckItem(BaseModel):
    name: str
    passed: bool
    score: int
    max_score: int
    message: str
    examples: List[str] = []


class GEOAnalyzeResponse(BaseModel):
    geo_score: int
    max_score: int
    grade: str
    word_count: int
    checks: List[GEOCheckItem]
    recommendations: List[str]
    structure_summary: dict


class GEOOptimizeResponse(BaseModel):
    topic: str
    suggested_definition: str
    qa_pairs: List[dict]
    citation_templates: List[str]
    statistic_templates: List[str]
    suggested_structure: str
    tips: List[str]


class GEOCitationResponse(BaseModel):
    citation_enhancements: List[dict]
    statistic_opportunities: List[dict]
    current_citation_count: int
    current_statistic_count: int
