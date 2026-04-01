"""
Semantic validation - description quality, name quality, schema logic.
"""

from typing import Any, Dict, List
import re
from app.models import ErrorDetail, WarningDetail


FORBIDDEN_PHRASES = [
    "ai tool",
    "does smart things",
    "uses machine learning",
    "leverages ai",
    "intelligent system",
]

FUNCTIONAL_KEYWORDS = [
    "extractor",
    "converter",
    "validator",
    "generator",
    "parser",
    "classifier",
    "transformer",
    "aggregator",
    "filter",
    "mapper",
    "encoder",
    "decoder",
    "analyzer",
    "builder",
    "processor",
]


def validate_description_quality(skill_data: Dict[str, Any]) -> List[ErrorDetail]:
    """Validate description has clear action, input/output, and constraints."""
    errors = []

    if "description" not in skill_data:
        return errors

    desc = skill_data["description"].lower() if isinstance(skill_data["description"], str) else ""

    # Check forbidden phrases
    for phrase in FORBIDDEN_PHRASES:
        if phrase in desc:
            errors.append(
                ErrorDetail(
                    field="description",
                    rule="VAGUE_DESCRIPTION",
                    message=f"Description contains generic phrase '{phrase}'. Be specific about functionality.",
                    severity="ERROR",
                )
            )

    # Check for action verb
    if not re.search(r"\b(generates?|creates?|validates?|extracts?|transforms?|converts?|parses?|filters?|analyzes?|builds?|processes?|classifies?|encodes?|decodes?)\b", desc, re.IGNORECASE):
        errors.append(
            ErrorDetail(
                field="description",
                rule="NO_ACTION_VERB",
                message="Description must contain a clear action verb (e.g., generates, validates, extracts)",
                severity="ERROR",
            )
        )

    # Check sentence count (max 3)
    sentences = re.split(r'[.!?]+', desc)
    sentences = [s.strip() for s in sentences if s.strip()]
    if len(sentences) > 3:
        errors.append(
            ErrorDetail(
                field="description",
                rule="TOO_LONG",
                message=f"Description should be ≤ 3 sentences (current: {len(sentences)})",
                severity="ERROR",
            )
        )

    return errors


def validate_name_quality(skill_data: Dict[str, Any]) -> List[ErrorDetail]:
    """Validate name has functional meaning."""
    errors = []

    if "name" not in skill_data:
        return errors

    name = skill_data["name"]
    if not isinstance(name, str):
        return errors

    # Check word count (at least 3 words for functional names)
    words = name.split()
    if len(words) < 2:
        errors.append(
            ErrorDetail(
                field="name",
                rule="INSUFFICIENT_WORDS",
                message="Name should contain at least 2 words for clarity",
                severity="ERROR",
            )
        )

    # Check for functional keyword
    name_lower = name.lower()
    has_functional_keyword = any(keyword in name_lower for keyword in FUNCTIONAL_KEYWORDS)

    if not has_functional_keyword:
        errors.append(
            ErrorDetail(
                field="name",
                rule="NO_FUNCTIONAL_KEYWORD",
                message=f"Name must contain a functional keyword: {', '.join(FUNCTIONAL_KEYWORDS[:5])}...",
                severity="ERROR",
            )
        )

    # Check for generic names
    generic_words = ["tool", "ai", "smart", "system"]
    if any(word in name_lower for word in generic_words):
        # If it's JUST a generic word without functional meaning, flag it
        if len(words) < 3:
            errors.append(
                ErrorDetail(
                    field="name",
                    rule="GENERIC_NAME",
                    message=f"Name should be specific, not just '{name}'",
                    severity="ERROR",
                )
            )

    return errors


def validate_schema_semantic(skill_data: Dict[str, Any]) -> List[ErrorDetail]:
    """Validate input and output schemas have semantic difference."""
    errors = []

    if "input_schema" not in skill_data or "output_schema" not in skill_data:
        return errors

    input_schema = skill_data["input_schema"]
    output_schema = skill_data["output_schema"]

    if not isinstance(input_schema, dict) or not isinstance(output_schema, dict):
        return errors

    # Check if schemas are identical
    if input_schema == output_schema:
        errors.append(
            ErrorDetail(
                field="schema",
                rule="IDENTICAL_SCHEMAS",
                message="Input and output schemas must be different (skill must transform data)",
                severity="ERROR",
            )
        )

    # Check if output has at least some different keys
    input_keys = set(input_schema.keys())
    output_keys = set(output_schema.keys())

    if len(output_keys) == 0:
        errors.append(
            ErrorDetail(
                field="output_schema",
                rule="EMPTY_OUTPUT",
                message="Output schema cannot be empty",
                severity="ERROR",
            )
        )

    # Warn if schemas are too similar (all keys the same)
    if input_keys == output_keys and len(input_keys) > 0:
        errors.append(
            ErrorDetail(
                field="schema",
                rule="NO_TRANSFORMATION",
                message="Output schema should differ from input schema (add/remove/modify keys)",
                severity="ERROR",
            )
        )

    return errors


def validate_example_alignment(skill_data: Dict[str, Any]) -> List[ErrorDetail]:
    """Validate examples have matching keys with schemas."""
    errors = []

    if "examples" not in skill_data or not isinstance(skill_data["examples"], list):
        return errors

    if len(skill_data["examples"]) == 0:
        return errors

    input_schema = skill_data.get("input_schema", {})
    output_schema = skill_data.get("output_schema", {})

    if not isinstance(input_schema, dict) or not isinstance(output_schema, dict):
        return errors

    for idx, example in enumerate(skill_data["examples"]):
        if not isinstance(example, dict):
            errors.append(
                ErrorDetail(
                    field=f"examples[{idx}]",
                    rule="INVALID_EXAMPLE",
                    message="Each example must be a dict with 'input' and 'output' keys",
                    severity="ERROR",
                )
            )
            continue

        if "input" not in example or "output" not in example:
            errors.append(
                ErrorDetail(
                    field=f"examples[{idx}]",
                    rule="MISSING_EXAMPLE_KEYS",
                    message="Each example must have 'input' and 'output' keys",
                    severity="ERROR",
                )
            )
            continue

        # Validate input matches input_schema keys
        ex_input = example.get("input", {})
        if isinstance(ex_input, dict):
            input_keys = set(ex_input.keys())
            schema_input_keys = set(input_schema.keys())
            if not input_keys.issubset(schema_input_keys):
                missing = input_keys - schema_input_keys
                errors.append(
                    ErrorDetail(
                        field=f"examples[{idx}].input",
                        rule="SCHEMA_MISMATCH",
                        message=f"Example input keys {list(missing)} not in input_schema",
                        severity="ERROR",
                    )
                )

        # Validate output matches output_schema keys
        ex_output = example.get("output", {})
        if isinstance(ex_output, dict):
            output_keys = set(ex_output.keys())
            schema_output_keys = set(output_schema.keys())
            if not output_keys.issubset(schema_output_keys):
                missing = output_keys - schema_output_keys
                errors.append(
                    ErrorDetail(
                        field=f"examples[{idx}].output",
                        rule="SCHEMA_MISMATCH",
                        message=f"Example output keys {list(missing)} not in output_schema",
                        severity="ERROR",
                    )
                )

    return errors


def run_semantic_validation(skill_data: Dict[str, Any]) -> List[ErrorDetail]:
    """Run all semantic validations."""
    errors = []
    errors.extend(validate_description_quality(skill_data))
    errors.extend(validate_name_quality(skill_data))
    errors.extend(validate_schema_semantic(skill_data))
    errors.extend(validate_example_alignment(skill_data))
    return errors
