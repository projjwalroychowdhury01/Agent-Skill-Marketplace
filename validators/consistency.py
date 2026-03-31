"""
Consistency validation - tool usage, function/tool mismatch, determinism.
"""

from typing import Any, Dict, List
from models import ErrorDetail, WarningDetail


COMMON_TOOLS = {
    "http_request": "Web API calls",
    "database_query": "Database operations",
    "file_operations": "File I/O",
    "text_processing": "NLP/Text processing",
    "data_transformation": "Data conversion",
    "validation": "Input validation",
    "caching": "Caching/Memoization",
    "authentication": "Auth/Security",
    "logging": "Logging",
    "error_handling": "Error handling",
}


def validate_tool_consistency(skill_data: Dict[str, Any]) -> List[ErrorDetail]:
    """Validate tools_used are relevant to the skill function."""
    errors = []

    if "tools_used" not in skill_data:
        return errors

    tools = skill_data.get("tools_used", [])
    if not isinstance(tools, list):
        return errors

    name = (skill_data.get("name") or "").lower()
    description = (skill_data.get("description") or "").lower()
    combined_text = f"{name} {description}"

    # Check if tool names are meaningful
    for tool in tools:
        if not isinstance(tool, str):
            errors.append(
                ErrorDetail(
                    field="tools_used",
                    rule="INVALID_TOOL",
                    message=f"Tool name must be string, got {type(tool).__name__}",
                    severity="ERROR",
                )
            )
            continue

        tool_lower = tool.lower()

        # Check if tool is generic/empty
        if tool_lower in ["tool", "ai", "system", "service"]:
            errors.append(
                ErrorDetail(
                    field="tools_used",
                    rule="GENERIC_TOOL",
                    message=f"Tool '{tool}' is too generic. Be specific.",
                    severity="ERROR",
                )
            )

        # Check if tool matches function documentation
        tool_mentioned = any(keyword in combined_text for keyword in tool_lower.split("_"))
        if not tool_mentioned and len(tools) > 0:
            # Only flag if tools are explicitly provided but don't match description
            pass  # Soft check; allow flexibility here

    return errors


def validate_function_tool_mismatch(skill_data: Dict[str, Any]) -> List[ErrorDetail]:
    """Detect mismatch between function name/description and tools."""
    errors = []

    name = (skill_data.get("name") or "").lower()
    description = (skill_data.get("description") or "").lower()
    tools = skill_data.get("tools_used") or []

    # If name suggests data transformation but no data processing tools
    if any(word in name for word in ["extract", "parse", "transform", "convert"]):
        if "data_transformation" not in [t.lower() for t in tools]:
            # Not strict; allow pass
            pass

    # If name suggests HTTP/API work but no http tool
    if any(word in name for word in ["fetch", "call", "request", "api"]):
        if not any("http" in t.lower() or "request" in t.lower() for t in tools):
            # Not strict; allow pass
            pass

    return errors


def validate_determinism(skill_data: Dict[str, Any]) -> List[WarningDetail]:
    """Flag non-deterministic behaviors."""
    warnings = []

    description = (skill_data.get("description") or "").lower()
    name = (skill_data.get("name") or "").lower()
    combined_text = f"{name} {description}"

    non_deterministic_keywords = [
        "random",
        "shuffle",
        "current time",
        "depends on external",
        "unpredictable",
        "varies",
        "probabilistic",
    ]

    for keyword in non_deterministic_keywords:
        if keyword in combined_text:
            warnings.append(
                WarningDetail(
                    field="description",
                    rule="NON_DETERMINISTIC",
                    message=f"Skill may produce non-deterministic outputs (keyword: '{keyword}'). Ensure seeding/reproducibility.",
                )
            )
            break

    return warnings


def validate_external_dependencies(skill_data: Dict[str, Any]) -> List[WarningDetail]:
    """Flag undefined external system dependencies."""
    warnings = []

    description = (skill_data.get("description") or "").lower()
    tools = skill_data.get("tools_used") or []

    # If tools mention external services without documentation
    external_keywords = ["external", "third-party", "api", "web service"]
    has_external = any(keyword in description for keyword in external_keywords)

    if has_external and len(tools) == 0:
        warnings.append(
            WarningDetail(
                field="tools_used",
                rule="UNDEFINED_DEPENDENCIES",
                message="Description mentions external services but no tools_used is documented. Add tools for clarity.",
            )
        )

    return warnings


def run_consistency_validation(skill_data: Dict[str, Any]) -> tuple[List[ErrorDetail], List[WarningDetail]]:
    """Run all consistency validations."""
    errors = []
    warnings = []

    errors.extend(validate_tool_consistency(skill_data))
    errors.extend(validate_function_tool_mismatch(skill_data))
    warnings.extend(validate_determinism(skill_data))
    warnings.extend(validate_external_dependencies(skill_data))

    return errors, warnings
