"""
Structural validation - checks schema, types, and required fields.
"""

from typing import Any, Dict, List
from models import ErrorDetail


def validate_required_fields(skill_data: Dict[str, Any]) -> List[ErrorDetail]:
    """Validate all required fields exist."""
    errors = []
    required_fields = [
        "name",
        "description",
        "category",
        "tags",
        "input_schema",
        "output_schema",
    ]

    for field in required_fields:
        if field not in skill_data:
            errors.append(
                ErrorDetail(
                    field=field,
                    rule="REQUIRED_FIELD",
                    message=f"Missing required field: {field}",
                    severity="CRITICAL",
                )
            )

    return errors


def validate_field_types(skill_data: Dict[str, Any]) -> List[ErrorDetail]:
    """Validate field types."""
    errors = []
    type_rules = {
        "name": str,
        "description": str,
        "category": str,
        "tags": list,
        "input_schema": dict,
        "output_schema": dict,
        "examples": (list, type(None)),
        "tools_used": (list, type(None)),
        "source": (str, type(None)),
        "author": (str, type(None)),
    }

    for field, expected_type in type_rules.items():
        if field in skill_data and skill_data[field] is not None:
            value = skill_data[field]
            if isinstance(expected_type, tuple):
                if not isinstance(value, expected_type):
                    errors.append(
                        ErrorDetail(
                            field=field,
                            rule="TYPE_MISMATCH",
                            message=f"Field '{field}' must be {expected_type}, got {type(value).__name__}",
                            severity="CRITICAL",
                        )
                    )
            else:
                if not isinstance(value, expected_type):
                    errors.append(
                        ErrorDetail(
                            field=field,
                            rule="TYPE_MISMATCH",
                            message=f"Field '{field}' must be {expected_type.__name__}, got {type(value).__name__}",
                            severity="CRITICAL",
                        )
                    )

    return errors


def validate_field_constraints(skill_data: Dict[str, Any]) -> List[ErrorDetail]:
    """Validate field length and count constraints."""
    errors = []

    # Name constraint: <= 60 chars
    if "name" in skill_data and isinstance(skill_data["name"], str):
        if len(skill_data["name"]) > 60:
            errors.append(
                ErrorDetail(
                    field="name",
                    rule="LENGTH_CONSTRAINT",
                    message=f"Name exceeds 60 characters (current: {len(skill_data['name'])})",
                    severity="ERROR",
                )
            )
        if len(skill_data["name"]) < 3:
            errors.append(
                ErrorDetail(
                    field="name",
                    rule="LENGTH_CONSTRAINT",
                    message="Name must be at least 3 characters",
                    severity="ERROR",
                )
            )

    # Description constraint: <= 300 chars
    if "description" in skill_data and isinstance(skill_data["description"], str):
        if len(skill_data["description"]) > 300:
            errors.append(
                ErrorDetail(
                    field="description",
                    rule="LENGTH_CONSTRAINT",
                    message=f"Description exceeds 300 characters (current: {len(skill_data['description'])})",
                    severity="ERROR",
                )
            )

    # Tags constraint: 3-6 tags
    if "tags" in skill_data and isinstance(skill_data["tags"], list):
        if len(skill_data["tags"]) < 3:
            errors.append(
                ErrorDetail(
                    field="tags",
                    rule="COUNT_CONSTRAINT",
                    message=f"Must have at least 3 tags (current: {len(skill_data['tags'])})",
                    severity="ERROR",
                )
            )
        if len(skill_data["tags"]) > 6:
            errors.append(
                ErrorDetail(
                    field="tags",
                    rule="COUNT_CONSTRAINT",
                    message=f"Maximum 6 tags allowed (current: {len(skill_data['tags'])})",
                    severity="ERROR",
                )
            )

    return errors


def validate_json_validity(skill_data: Dict[str, Any]) -> List[ErrorDetail]:
    """Validate that schemas are valid JSON."""
    errors = []

    schema_fields = ["input_schema", "output_schema"]
    for field in schema_fields:
        if field in skill_data:
            schema = skill_data[field]
            if not isinstance(schema, dict):
                errors.append(
                    ErrorDetail(
                        field=field,
                        rule="INVALID_JSON",
                        message=f"{field} must be a valid JSON object (dict)",
                        severity="CRITICAL",
                    )
                )
            elif len(schema) == 0:
                errors.append(
                    ErrorDetail(
                        field=field,
                        rule="EMPTY_SCHEMA",
                        message=f"{field} cannot be empty",
                        severity="ERROR",
                    )
                )

    return errors


def validate_reserved_keywords(skill_data: Dict[str, Any]) -> List[ErrorDetail]:
    """Check for reserved keywords in field names."""
    errors = []
    reserved = {"id", "created_at", "updated_at", "system"}

    # Check in input_schema keys
    if "input_schema" in skill_data and isinstance(skill_data["input_schema"], dict):
        for key in skill_data["input_schema"].keys():
            if key in reserved:
                errors.append(
                    ErrorDetail(
                        field="input_schema",
                        rule="RESERVED_KEYWORD",
                        message=f"'{key}' is a reserved keyword and cannot be used in schema",
                        severity="ERROR",
                    )
                )

    # Check in output_schema keys
    if "output_schema" in skill_data and isinstance(skill_data["output_schema"], dict):
        for key in skill_data["output_schema"].keys():
            if key in reserved:
                errors.append(
                    ErrorDetail(
                        field="output_schema",
                        rule="RESERVED_KEYWORD",
                        message=f"'{key}' is a reserved keyword and cannot be used in schema",
                        severity="ERROR",
                    )
                )

    return errors


def run_structural_validation(skill_data: Dict[str, Any]) -> List[ErrorDetail]:
    """Run all structural validations."""
    errors = []
    errors.extend(validate_required_fields(skill_data))
    errors.extend(validate_field_types(skill_data))
    errors.extend(validate_field_constraints(skill_data))
    errors.extend(validate_json_validity(skill_data))
    errors.extend(validate_reserved_keywords(skill_data))
    return errors
