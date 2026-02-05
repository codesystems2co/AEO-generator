import re
from app.schemas import AEORequest, AEResponse, AEOQuestionAnswer


def _title_from_topic(topic: str) -> str:
    t = topic.strip()
    if not t:
        return "Untitled"
    return t[0].upper() + t[1:] if len(t) > 1 else t.upper()


def generate_aeo_suggestions(req: AEORequest) -> AEResponse:
    topic = req.topic.strip().lower()
    context = (req.context or "").strip()
    
    suggested_title = _title_from_topic(req.topic)
    summary = f"A comprehensive guide covering {req.topic}. " + (
        context if context else "Optimized for both search engines and AI answer engines."
    )
    
    key_entities = []
    for word in re.findall(r"\b[a-z]{4,}\b", topic):
        if word not in {"what", "how", "when", "where", "why", "guide", "best", "top"}:
            key_entities.append(word.title())
    if not key_entities:
        key_entities = [req.topic.strip().title()]
    
    questions_answers = []
    if req.include_qa:
        qa_templates = [
            (f"What is {req.topic}?", f"{req.topic.title()} refers to the concepts and practices related to this topic. This guide explains the key points in detail."),
            (f"How does {req.topic} work?", "This section breaks down the main mechanisms and steps involved."),
            (f"Why is {req.topic} important?", "Understanding this topic helps with better decisions and outcomes in practice."),
        ]
        for q, a in qa_templates[:3]:
            questions_answers.append(AEOQuestionAnswer(question=q, answer=a))
    
    structured_sections = [
        f"Introduction to {req.topic.title()}",
        "Key concepts and definitions",
        "Step-by-step or main points",
        "Examples and use cases",
        "Best practices and tips",
        "Summary and next steps",
    ]
    
    tips = [
        "Use clear, factual sentences—AI answer engines favor concise, authoritative content.",
        "Include a short summary or definition in the first paragraph.",
        "Add FAQ-style Q&A blocks to match how people ask questions in ChatGPT/Perplexity.",
        "Use proper headings (H2, H3) so both crawlers and LLMs can parse structure.",
        "Mention key entities and terms consistently for entity-based retrieval.",
    ]
    
    return AEResponse(
        suggested_title=suggested_title,
        summary=summary,
        key_entities=key_entities[:10],
        questions_answers=questions_answers,
        structured_sections=structured_sections,
        tips=tips,
    )
