from app.schemas import SEOScoreRequest, SEOScoreResponse, ScoreItem


def _grade(score: int, max_score: int) -> str:
    pct = 100 * score / max_score if max_score else 0
    if pct >= 90:
        return "A"
    if pct >= 80:
        return "B"
    if pct >= 70:
        return "C"
    if pct >= 60:
        return "D"
    return "F"


def calculate_seo_score(req: SEOScoreRequest) -> SEOScoreResponse:
    checks = []
    score = 0
    max_score = 0
    
    # Title length 30–60
    max_score += 15
    title_len = len(req.title.strip())
    if 30 <= title_len <= 60:
        score += 15
        checks.append(ScoreItem(name="Title length (30–60 chars)", score=15, max_score=15, passed=True, message=f"Title has {title_len} characters."))
    elif 20 <= title_len <= 70:
        score += 10
        checks.append(ScoreItem(name="Title length (30–60 chars)", score=10, max_score=15, passed=False, message=f"Title has {title_len} characters. Aim for 30–60."))
    else:
        checks.append(ScoreItem(name="Title length (30–60 chars)", score=0, max_score=15, passed=False, message=f"Title has {title_len} characters. Aim for 30–60."))
    
    # Meta description 120–160
    max_score += 15
    meta_len = len(req.meta_description.strip())
    if 120 <= meta_len <= 160:
        score += 15
        checks.append(ScoreItem(name="Meta description (120–160 chars)", score=15, max_score=15, passed=True, message=f"Description has {meta_len} characters."))
    elif 100 <= meta_len <= 180:
        score += 10
        checks.append(ScoreItem(name="Meta description (120–160 chars)", score=10, max_score=15, passed=False, message=f"Description has {meta_len} characters. Aim for 120–160."))
    else:
        checks.append(ScoreItem(name="Meta description (120–160 chars)", score=0, max_score=15, passed=False, message=f"Description has {meta_len} characters. Aim for 120–160."))
    
    # Content length
    max_score += 20
    words = len(req.content.split())
    if words >= 1000:
        score += 20
        checks.append(ScoreItem(name="Content length (1000+ words)", score=20, max_score=20, passed=True, message=f"Content has {words} words."))
    elif words >= 300:
        score += 12
        checks.append(ScoreItem(name="Content length (1000+ words)", score=12, max_score=20, passed=False, message=f"Content has {words} words. 1000+ is ideal."))
    else:
        checks.append(ScoreItem(name="Content length (1000+ words)", score=0, max_score=20, passed=False, message=f"Content has {words} words. Add more for better SEO."))
    
    # Title has content
    max_score += 15
    if req.title.strip():
        score += 15
        checks.append(ScoreItem(name="Title present", score=15, max_score=15, passed=True, message="Title is set."))
    else:
        checks.append(ScoreItem(name="Title present", score=0, max_score=15, passed=False, message="Add a descriptive title."))
    
    # Meta present
    max_score += 15
    if req.meta_description.strip():
        score += 15
        checks.append(ScoreItem(name="Meta description present", score=15, max_score=15, passed=True, message="Meta description is set."))
    else:
        checks.append(ScoreItem(name="Meta description present", score=0, max_score=15, passed=False, message="Add a meta description."))
    
    # Headings (simple check)
    max_score += 10
    lines = req.content.split("\n")
    heading_like = sum(1 for l in lines if l.strip().startswith("#") or (len(l) < 80 and ":" in l and l.strip()[0].isupper()))
    if heading_like >= 3:
        score += 10
        checks.append(ScoreItem(name="Headings / structure", score=10, max_score=10, passed=True, message=f"Found {heading_like} heading-like lines."))
    elif heading_like >= 1:
        score += 5
        checks.append(ScoreItem(name="Headings / structure", score=5, max_score=10, passed=False, message="Add more H2/H3 headings."))
    else:
        checks.append(ScoreItem(name="Headings / structure", score=0, max_score=10, passed=False, message="Add clear headings for structure."))
    
    # URL (optional)
    max_score += 10
    if req.url and req.url.strip().startswith("http"):
        score += 10
        checks.append(ScoreItem(name="URL format", score=10, max_score=10, passed=True, message="Valid URL provided."))
    else:
        score += 5
        checks.append(ScoreItem(name="URL format", score=5, max_score=10, passed=False, message="Optional: add canonical URL."))
    
    recommendations = []
    if title_len < 30 or title_len > 60:
        recommendations.append("Adjust title to 30–60 characters for best SERP display.")
    if meta_len < 120 or meta_len > 160:
        recommendations.append("Set meta description to 120–160 characters.")
    if words < 300:
        recommendations.append("Write at least 300 words; 1000+ is better for competitive terms.")
    if heading_like < 2:
        recommendations.append("Use H2/H3 headings to structure the page.")
    
    return SEOScoreResponse(
        overall_score=score,
        max_score=max_score,
        grade=_grade(score, max_score),
        checks=checks,
        recommendations=recommendations,
    )
