"""
Normalization - standardizes and cleans skill data.
"""

from typing import Any, Dict, List


SYNONYM_MAP = {
    "nlp": "natural language processing",
    "ml": "machine learning",
    "dl": "deep learning",
    "db": "database",
    "api": "application programming interface",
    "http": "hypertext transfer protocol",
    "json": "javascript object notation",
    "xml": "extensible markup language",
    "csv": "comma separated values",
    "sql": "structured query language",
    "ai": "artificial intelligence",
    "etl": "extract transform load",
    "ml": "machine learning",
    "cv": "computer vision",
    "llm": "large language model",
}

CONTROLLED_TAGS = {
    "data extraction",
    "data transformation",
    "data validation",
    "text processing",
    "image processing",
    "api integration",
    "database operations",
    "authentication",
    "content generation",
    "classification",
    "prediction",
    "analysis",
    "aggregation",
    "filtering",
    "sorting",
    "mapping",
    "encoding",
    "decoding",
    "parsing",
    "formatting",
}


def normalize_strings(skill_data: Dict[str, Any]) -> Dict[str, Any]:
    """Trim and standardize string fields."""
    normalized = skill_data.copy()

    string_fields = ["name", "description", "category", "author", "source"]
    for field in string_fields:
        if field in normalized and isinstance(normalized[field], str):
            normalized[field] = normalized[field].strip()

    return normalized


def normalize_tags(skill_data: Dict[str, Any]) -> Dict[str, Any]:
    """Lowercase, deduplicate, and normalize tag synonyms."""
    normalized = skill_data.copy()

    if "tags" not in normalized or not isinstance(normalized["tags"], list):
        return normalized

    tags = normalized["tags"]
    normalized_tags = []

    for tag in tags:
        if not isinstance(tag, str):
            continue

        # Strip whitespace
        tag = tag.strip()

        # Lowercase
        tag_lower = tag.lower()

        # Replace synonyms
        if tag_lower in SYNONYM_MAP:
            tag_lower = SYNONYM_MAP[tag_lower]

        # Deduplicate
        if tag_lower not in normalized_tags:
            normalized_tags.append(tag_lower)

    normalized["tags"] = normalized_tags
    return normalized


def normalize_examples(skill_data: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure examples have consistent structure."""
    normalized = skill_data.copy()

    if "examples" not in normalized or not isinstance(normalized["examples"], list):
        return normalized

    normalized_examples = []
    for example in normalized["examples"]:
        if isinstance(example, dict):
            # Ensure 'input' and 'output' keys exist
            normalized_examples.append({
                "input": example.get("input", {}),
                "output": example.get("output", {}),
            })

    normalized["examples"] = normalized_examples
    return normalized


def normalize_schemas(skill_data: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure schemas are well-formed."""
    normalized = skill_data.copy()

    # Schemas are already validated, just ensure they exist
    if "input_schema" not in normalized:
        normalized["input_schema"] = {}
    if "output_schema" not in normalized:
        normalized["output_schema"] = {}

    return normalized


def normalize_tools(skill_data: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize tools list."""
    normalized = skill_data.copy()

    if "tools_used" not in normalized:
        normalized["tools_used"] = []

    if isinstance(normalized["tools_used"], list):
        # Trim, lowercase, deduplicate
        tools = normalized["tools_used"]
        normalized_tools = []
        for tool in tools:
            if isinstance(tool, str):
                tool = tool.strip().lower()
                if tool and tool not in normalized_tools:
                    normalized_tools.append(tool)
        normalized["tools_used"] = normalized_tools
    else:
        normalized["tools_used"] = []

    return normalized


def suggest_tag_corrections(tags: List[str]) -> Dict[str, str]:
    """Suggest corrections for uncontrolled tags."""
    suggestions = {}

    controlled_lower = {tag.lower(): tag for tag in CONTROLLED_TAGS}

    for tag in tags:
        tag_lower = tag.lower()
        if tag_lower not in controlled_lower:
            # Find closest match (simple substring match)
            for controlled in CONTROLLED_TAGS:
                if tag_lower in controlled.lower() or controlled.lower() in tag_lower:
                    suggestions[tag] = controlled
                    break

    return suggestions


def run_normalization(skill_data: Dict[str, Any]) -> Dict[str, Any]:
    """Run all normalization steps."""
    normalized = skill_data.copy()
    normalized = normalize_strings(normalized)
    normalized = normalize_tags(normalized)
    normalized = normalize_examples(normalized)
    normalized = normalize_schemas(normalized)
    normalized = normalize_tools(normalized)
    return normalized
