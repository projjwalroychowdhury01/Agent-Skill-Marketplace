"""
Quality scoring - calculates skill quality metrics.
"""

from typing import Any, Dict
import re
from app.models import ScoreBreakdown


def score_description_quality(skill_data: Dict[str, Any]) -> int:
    """Score description: 0-20 points."""
    score = 0
    max_score = 20

    description = skill_data.get("description") or ""
    if not isinstance(description, str):
        return 0

    # Full points for having description
    score += 5

    # Length bonus (not too short, not too long)
    if 50 <= len(description) <= 250:
        score += 5
    elif 30 <= len(description) <= 300:
        score += 3

    # Action verb bonus
    if re.search(r"\b(generates?|creates?|validates?|extracts?|transforms?|converts?|parses?|filters?|analyzes?|builds?|processes?)\b", description, re.IGNORECASE):
        score += 5

    # Clear structure (mentions input/output)
    if "input" in description.lower() or "receives" in description.lower():
        score += 3
    if "output" in description.lower() or "returns" in description.lower():
        score += 3

    return min(score, max_score)


def score_example_quality(skill_data: Dict[str, Any]) -> int:
    """Score examples: 0-15 points."""
    score = 0
    max_score = 15

    examples = skill_data.get("examples") or []
    if not isinstance(examples, list):
        return 0

    # Points for having examples
    if len(examples) > 0:
        score += 5

    # Points for multiple examples
    if len(examples) >= 2:
        score += 5

    # Points for example with meaningful data
    for example in examples:
        if isinstance(example, dict):
            input_data = example.get("input", {})
            output_data = example.get("output", {})
            if isinstance(input_data, dict) and isinstance(output_data, dict):
                if len(input_data) > 0 and len(output_data) > 0:
                    score += 5
                    break

    return min(score, max_score)


def score_tag_quality(skill_data: Dict[str, Any]) -> int:
    """Score tags: 0-10 points."""
    score = 0
    max_score = 10

    tags = skill_data.get("tags") or []
    if not isinstance(tags, list):
        return 0

    # Points for having tags
    if len(tags) > 0:
        score += 3

    # Points for 3-6 tags (ideal range)
    if 3 <= len(tags) <= 6:
        score += 5

    # Points for tags that look meaningful (not generic)
    non_generic = 0
    generic_words = {"tool", "ai", "system", "service", "skill"}
    for tag in tags:
        if isinstance(tag, str):
            tag_lower = tag.lower()
            if not any(word in tag_lower for word in generic_words):
                non_generic += 1

    if non_generic >= 2:
        score += 2

    return min(score, max_score)


def score_schema_quality(skill_data: Dict[str, Any]) -> int:
    """Score schemas: 0-10 points."""
    score = 0
    max_score = 10

    input_schema = skill_data.get("input_schema") or {}
    output_schema = skill_data.get("output_schema") or {}

    if not isinstance(input_schema, dict) or not isinstance(output_schema, dict):
        return 0

    # Points for having schemas
    if len(input_schema) > 0:
        score += 3
    if len(output_schema) > 0:
        score += 3

    # Points for schema diversity (multiple fields)
    total_fields = len(input_schema) + len(output_schema)
    if total_fields >= 2:
        score += 2
    if total_fields >= 4:
        score += 2

    return min(score, max_score)


def score_naming_quality(skill_data: Dict[str, Any]) -> int:
    """Score naming: 0-10 points."""
    score = 0
    max_score = 10

    name = skill_data.get("name") or ""
    if not isinstance(name, str):
        return 0

    # Points for having a name
    score += 2

    # Points for appropriate length
    if 5 <= len(name) <= 50:
        score += 3

    # Points for functional keywords
    functional_keywords = [
        "extractor", "converter", "validator", "generator", "parser",
        "classifier", "transformer", "aggregator", "filter", "mapper"
    ]
    if any(keyword in name.lower() for keyword in functional_keywords):
        score += 4

    # Points for multiple words
    words = name.split()
    if len(words) >= 2:
        score += 1

    return min(score, max_score)


def score_consistency_quality(skill_data: Dict[str, Any]) -> int:
    """Score consistency: 0-10 points."""
    score = 0
    max_score = 10

    # Points for coherent skill description
    name = (skill_data.get("name") or "").lower()
    description = (skill_data.get("description") or "").lower()

    # Check if name and description are related
    name_words = set(name.split())
    description_words = set(description.split())

    overlap = name_words & description_words
    if len(overlap) > 0:
        score += 3

    # Points for having tools defined
    tools = skill_data.get("tools_used") or []
    if isinstance(tools, list) and len(tools) > 0:
        score += 3

    # Points for having examples
    examples = skill_data.get("examples") or []
    if isinstance(examples, list) and len(examples) > 0:
        score += 2

    # Points for input/output difference (good transformation)
    input_schema = skill_data.get("input_schema") or {}
    output_schema = skill_data.get("output_schema") or {}
    if isinstance(input_schema, dict) and isinstance(output_schema, dict):
        if len(input_schema) > 0 and input_schema != output_schema:
            score += 2

    return min(score, max_score)


def calculate_quality_score(skill_data: Dict[str, Any]) -> tuple[ScoreBreakdown, int]:
    """Calculate overall quality score (0-100)."""
    breakdown = ScoreBreakdown(
        description_quality=score_description_quality(skill_data),
        example_quality=score_example_quality(skill_data),
        tag_quality=score_tag_quality(skill_data),
        schema_quality=score_schema_quality(skill_data),
        naming_quality=score_naming_quality(skill_data),
        consistency_quality=score_consistency_quality(skill_data),
    )

    total = (
        breakdown.description_quality
        + breakdown.example_quality
        + breakdown.tag_quality
        + breakdown.schema_quality
        + breakdown.naming_quality
        + breakdown.consistency_quality
    )

    breakdown.total = total

    return breakdown, total
