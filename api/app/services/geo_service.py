"""
GEO (Generative Engine Optimization) Service

Provides analysis and suggestions for optimizing content for AI-powered
generative search engines like ChatGPT, Perplexity, Google AI Overviews,
and Microsoft Copilot.

Based on research showing that GEO techniques can improve visibility in
AI-generated responses by focusing on: citations, quotability, statistics,
authoritative language, fluency, and structured content.
"""

import re
from typing import List, Optional
from app.schemas import (
    GEOAnalyzeRequest, GEOAnalyzeResponse, GEOCheckItem,
    GEOOptimizeRequest, GEOOptimizeResponse,
    GEOCitationRequest, GEOCitationResponse,
)


# Patterns for GEO analysis
STATISTIC_PATTERNS = [
    r'\b\d+(?:\.\d+)?%',  # Percentages
    r'\b\d+(?:,\d{3})+\b',  # Large numbers with commas
    r'\b(?:million|billion|trillion)\b',
    r'\b\d+x\b',  # Multipliers like "10x"
    r'\b(?:doubled|tripled|increased by|decreased by)\s+\d+',
    r'\b\d+\s+(?:times|percent|points)\b',
]

CITATION_PATTERNS = [
    r'according to\s+[A-Z]',
    r'(?:research|study|survey|report|data)\s+(?:by|from|shows|indicates)',
    r'\(\d{4}\)',  # Year citations like (2024)
    r'(?:et al\.|Ph\.D\.|Dr\.|Prof\.)',
    r'[A-Z][a-z]+\s+(?:University|Institute|Foundation|Journal)',
    r'published\s+(?:in|by)',
]

AUTHORITATIVE_PHRASES = [
    'research shows', 'studies indicate', 'experts recommend',
    'according to', 'data suggests', 'evidence shows',
    'scientifically proven', 'peer-reviewed', 'industry standard',
    'best practice', 'widely recognized', 'established',
]

QUOTABLE_INDICATORS = [
    r'^["\'].*["\']$',  # Quoted sentences
    r'(?:defined as|refers to|means that|is when)',  # Definitions
    r'^(?:The |A |An )?[A-Z][a-z]+(?:\s+[a-z]+){0,3}\s+is\s+',  # "X is Y" definitions
    r'(?:key|main|primary|essential|critical)\s+(?:factor|point|element|aspect)',
]

FLUENCY_ISSUES = [
    (r'\b(\w+)\s+\1\b', 'repeated word'),
    (r'[.!?]\s*[.!?]', 'double punctuation'),
    (r'\s{2,}', 'extra spaces'),
    (r'(?:very|really|basically|actually|literally)\s+(?:very|really)', 'filler words'),
]

# Question patterns that AI engines look for
QUESTION_PATTERNS = [
    r'^(?:What|How|Why|When|Where|Who|Which|Can|Does|Is|Are|Should|Would)\s+',
    r'\?$',
]


def _count_pattern_matches(text: str, patterns: List[str]) -> int:
    """Count how many patterns match in the text."""
    count = 0
    for pattern in patterns:
        count += len(re.findall(pattern, text, re.IGNORECASE | re.MULTILINE))
    return count


def _find_pattern_examples(text: str, patterns: List[str], max_examples: int = 5) -> List[str]:
    """Find example matches for patterns."""
    examples = []
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            if isinstance(match, tuple):
                match = match[0]
            if match and len(match) > 2 and match not in examples:
                examples.append(match.strip())
                if len(examples) >= max_examples:
                    return examples
    return examples


def _check_structure(text: str) -> dict:
    """Analyze content structure for GEO."""
    lines = text.split('\n')
    
    # Check for headings (markdown or title-case lines)
    headings = [l for l in lines if l.strip().startswith('#') or 
                (len(l) < 80 and l.strip() and l.strip()[0].isupper() and ':' in l)]
    
    # Check for lists
    list_items = [l for l in lines if re.match(r'^\s*[-*•]\s+', l) or re.match(r'^\s*\d+[.)]\s+', l)]
    
    # Check for short paragraphs (good for AI extraction)
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    short_paragraphs = [p for p in paragraphs if len(p.split()) <= 50]
    
    # Check for Q&A format
    questions = _count_pattern_matches(text, QUESTION_PATTERNS)
    
    return {
        'heading_count': len(headings),
        'list_item_count': len(list_items),
        'paragraph_count': len(paragraphs),
        'short_paragraph_ratio': len(short_paragraphs) / len(paragraphs) if paragraphs else 0,
        'question_count': questions,
        'has_qa_format': questions >= 2,
    }


def analyze_geo_content(req: GEOAnalyzeRequest) -> GEOAnalyzeResponse:
    """Analyze content for Generative Engine Optimization."""
    text = req.content
    word_count = len(text.split())
    checks = []
    recommendations = []
    
    # 1. Statistics and data
    stat_count = _count_pattern_matches(text, STATISTIC_PATTERNS)
    stat_examples = _find_pattern_examples(text, STATISTIC_PATTERNS)
    has_stats = stat_count >= 2
    checks.append(GEOCheckItem(
        name="Statistics and data",
        passed=has_stats,
        score=min(stat_count * 10, 20),
        max_score=20,
        message=f"Found {stat_count} statistical references." if stat_count else "No statistics or data points found.",
        examples=stat_examples,
    ))
    if not has_stats:
        recommendations.append("Add specific statistics, percentages, or data points to increase credibility and citability.")
    
    # 2. Citations and sources
    citation_count = _count_pattern_matches(text, CITATION_PATTERNS)
    citation_examples = _find_pattern_examples(text, CITATION_PATTERNS)
    has_citations = citation_count >= 2
    checks.append(GEOCheckItem(
        name="Citations and sources",
        passed=has_citations,
        score=min(citation_count * 10, 20),
        max_score=20,
        message=f"Found {citation_count} citation/source references." if citation_count else "No citations or source references found.",
        examples=citation_examples,
    ))
    if not has_citations:
        recommendations.append("Add citations like 'according to [source]', 'research shows', or reference specific studies/experts.")
    
    # 3. Authoritative language
    auth_count = sum(1 for phrase in AUTHORITATIVE_PHRASES if phrase.lower() in text.lower())
    has_authority = auth_count >= 2
    checks.append(GEOCheckItem(
        name="Authoritative language",
        passed=has_authority,
        score=min(auth_count * 5, 15),
        max_score=15,
        message=f"Found {auth_count} authoritative phrases." if auth_count else "Limited authoritative language.",
        examples=[p for p in AUTHORITATIVE_PHRASES if p.lower() in text.lower()][:5],
    ))
    if not has_authority:
        recommendations.append("Use authoritative phrases like 'research shows', 'experts recommend', 'data suggests'.")
    
    # 4. Quotable content (definitions, clear statements)
    quotable_count = _count_pattern_matches(text, QUOTABLE_INDICATORS)
    has_quotable = quotable_count >= 2
    checks.append(GEOCheckItem(
        name="Quotable definitions",
        passed=has_quotable,
        score=min(quotable_count * 5, 15),
        max_score=15,
        message=f"Found {quotable_count} quotable/definition patterns." if quotable_count else "Few clear definitions or quotable statements.",
        examples=_find_pattern_examples(text, QUOTABLE_INDICATORS),
    ))
    if not has_quotable:
        recommendations.append("Include clear definitions ('X is defined as...', 'X refers to...') that AI can easily quote.")
    
    # 5. Structure analysis
    structure = _check_structure(text)
    good_structure = (structure['heading_count'] >= 2 and 
                      structure['short_paragraph_ratio'] >= 0.5)
    checks.append(GEOCheckItem(
        name="AI-friendly structure",
        passed=good_structure,
        score=15 if good_structure else (8 if structure['heading_count'] >= 1 else 0),
        max_score=15,
        message=f"{structure['heading_count']} headings, {structure['list_item_count']} list items, {int(structure['short_paragraph_ratio']*100)}% short paragraphs.",
        examples=[],
    ))
    if not good_structure:
        recommendations.append("Use clear headings, bullet points, and short paragraphs (under 50 words) for easy AI extraction.")
    
    # 6. Q&A format
    has_qa = structure['has_qa_format']
    checks.append(GEOCheckItem(
        name="Q&A format",
        passed=has_qa,
        score=15 if has_qa else 0,
        max_score=15,
        message=f"Found {structure['question_count']} questions in content." if structure['question_count'] else "No Q&A format detected.",
        examples=[],
    ))
    if not has_qa:
        recommendations.append("Include FAQ-style Q&A sections that directly match how users query AI assistants.")
    
    # 7. Fluency check
    fluency_issues = []
    for pattern, issue_type in FLUENCY_ISSUES:
        if re.search(pattern, text, re.IGNORECASE):
            fluency_issues.append(issue_type)
    good_fluency = len(fluency_issues) == 0
    checks.append(GEOCheckItem(
        name="Fluency and clarity",
        passed=good_fluency,
        score=10 if good_fluency else 5,
        max_score=10,
        message="Text appears fluent and clear." if good_fluency else f"Potential issues: {', '.join(fluency_issues)}.",
        examples=fluency_issues,
    ))
    if not good_fluency:
        recommendations.append(f"Fix fluency issues: {', '.join(fluency_issues)}.")
    
    # Calculate overall score
    total_score = sum(c.score for c in checks)
    max_score = sum(c.max_score for c in checks)
    
    # Determine grade
    pct = (total_score / max_score * 100) if max_score else 0
    if pct >= 80:
        grade = "A"
    elif pct >= 65:
        grade = "B"
    elif pct >= 50:
        grade = "C"
    elif pct >= 35:
        grade = "D"
    else:
        grade = "F"
    
    return GEOAnalyzeResponse(
        geo_score=total_score,
        max_score=max_score,
        grade=grade,
        word_count=word_count,
        checks=checks,
        recommendations=recommendations,
        structure_summary=structure,
    )


def generate_geo_suggestions(req: GEOOptimizeRequest) -> GEOOptimizeResponse:
    """Generate GEO optimization suggestions for a topic."""
    topic = req.topic
    context = req.context or ""
    
    # Generate quotable definition
    definition = f"{topic.title()} refers to the process or concept of {topic.lower()}. It is widely recognized as an important aspect in its field."
    
    # Generate Q&A pairs
    qa_pairs = [
        {"question": f"What is {topic}?", "answer": f"{topic.title()} is [provide a clear, concise definition that AI can easily quote]."},
        {"question": f"Why is {topic} important?", "answer": f"{topic.title()} is important because [list 2-3 key benefits with supporting data]."},
        {"question": f"How does {topic} work?", "answer": f"{topic.title()} works by [explain the process in clear, step-by-step terms]."},
        {"question": f"What are the benefits of {topic}?", "answer": f"The main benefits of {topic} include: 1) [benefit with statistic], 2) [benefit with example], 3) [benefit with expert citation]."},
        {"question": f"What are best practices for {topic}?", "answer": f"According to industry experts, best practices for {topic} include: [list actionable recommendations]."},
    ]
    
    # Generate citation templates
    citation_templates = [
        f"According to [Source/Expert], {topic} [key finding or statistic].",
        f"Research from [Institution] shows that {topic} [measurable impact].",
        f"A [year] study published in [Journal] found that {topic} [specific result].",
        f"Industry data indicates that [X]% of [group] [action related to {topic}].",
        f"[Expert Name], [Title] at [Organization], states that \"{topic} [expert quote].\"",
    ]
    
    # Generate statistic templates
    statistic_templates = [
        f"[X]% of [target audience] report [benefit from {topic}].",
        f"Organizations using {topic} see an average [X]% improvement in [metric].",
        f"{topic.title()} can reduce [problem] by up to [X]%.",
        f"The {topic} market is projected to reach $[X] billion by [year].",
        f"[X] out of [Y] experts recommend {topic} for [use case].",
    ]
    
    # Suggested structure
    suggested_structure = [
        f"## What is {topic.title()}?",
        "[Clear definition - 1-2 sentences that AI can quote directly]",
        "",
        f"## Why {topic.title()} Matters",
        "[Key benefits with statistics and citations]",
        "",
        f"## How {topic.title()} Works",
        "[Step-by-step explanation with examples]",
        "",
        f"## Key Benefits of {topic.title()}",
        "- [Benefit 1 with data point]",
        "- [Benefit 2 with expert citation]",
        "- [Benefit 3 with case study reference]",
        "",
        f"## Best Practices for {topic.title()}",
        "[Actionable recommendations backed by research]",
        "",
        f"## Frequently Asked Questions About {topic.title()}",
        "[FAQ section with clear Q&A pairs]",
    ]
    
    # GEO tips
    tips = [
        "Start with a clear, quotable definition in the first paragraph.",
        "Include at least 3-5 specific statistics or data points.",
        "Add citations using 'according to [source]' or 'research shows'.",
        "Use FAQ format for common questions about your topic.",
        "Keep paragraphs short (under 50 words) for easy AI extraction.",
        "Include expert quotes or references to authoritative sources.",
        "Structure content with clear headings that match search queries.",
        "Provide concrete examples and case studies with measurable results.",
    ]
    
    return GEOOptimizeResponse(
        topic=topic,
        suggested_definition=definition,
        qa_pairs=qa_pairs,
        citation_templates=citation_templates,
        statistic_templates=statistic_templates,
        suggested_structure="\n".join(suggested_structure),
        tips=tips,
    )


def enhance_citations(req: GEOCitationRequest) -> GEOCitationResponse:
    """Suggest citation enhancements for content."""
    text = req.content
    sentences = re.split(r'[.!?]+', text)
    
    # Find sentences that could benefit from citations
    enhancement_candidates = []
    for sent in sentences:
        sent = sent.strip()
        if len(sent) < 20:
            continue
        
        # Check if sentence makes a claim without citation
        claim_indicators = [
            r'\b(?:studies|research|experts|data|evidence)\b',
            r'\b(?:most|many|few|all|none)\s+(?:people|users|companies|organizations)',
            r'\b(?:always|never|typically|usually|often|rarely)\b',
            r'\b(?:better|worse|more|less|higher|lower|faster|slower)\s+than\b',
            r'\b(?:increase|decrease|improve|reduce|grow|decline)\b',
        ]
        
        has_claim = any(re.search(p, sent, re.IGNORECASE) for p in claim_indicators)
        has_citation = any(re.search(p, sent, re.IGNORECASE) for p in CITATION_PATTERNS)
        
        if has_claim and not has_citation:
            # Suggest enhancement
            enhancement = f"According to [source], {sent.lower()}" if not sent[0].isupper() else f"Research shows that {sent[0].lower()}{sent[1:]}"
            enhancement_candidates.append({
                "original": sent,
                "suggestion": enhancement,
                "type": "Add citation",
            })
    
    # Find sentences that could use statistics
    stat_candidates = []
    for sent in sentences:
        sent = sent.strip()
        if len(sent) < 20:
            continue
        
        vague_indicators = [
            r'\b(?:significant|substantial|considerable|notable)\b',
            r'\b(?:many|most|some|few)\b',
            r'\b(?:often|sometimes|rarely|frequently)\b',
            r'\b(?:large|small|big|huge|tiny)\b',
        ]
        
        is_vague = any(re.search(p, sent, re.IGNORECASE) for p in vague_indicators)
        has_stat = any(re.search(p, sent) for p in STATISTIC_PATTERNS)
        
        if is_vague and not has_stat:
            stat_candidates.append({
                "original": sent,
                "suggestion": "Add specific numbers, percentages, or data points to quantify this claim.",
                "type": "Add statistic",
            })
    
    return GEOCitationResponse(
        citation_enhancements=enhancement_candidates[:10],
        statistic_opportunities=stat_candidates[:10],
        current_citation_count=_count_pattern_matches(text, CITATION_PATTERNS),
        current_statistic_count=_count_pattern_matches(text, STATISTIC_PATTERNS),
    )
