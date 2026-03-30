"""
Security validation - scans for dangerous patterns and compliance issues.
"""

from typing import Any, Dict, List
import re
from models import ErrorDetail, WarningDetail


DANGEROUS_PATTERNS = [
    ("execute shell", "Shell execution vulnerability"),
    ("run arbitrary code", "Code injection risk"),
    ("bypass security", "Security bypass attempt"),
    ("eval(", "Dynamic code evaluation"),
    ("exec(", "Dynamic code execution"),
    ("__import__", "Module import exploit"),
    ("subprocess", "Subprocess shell execution"),
    ("os.system", "OS shell execution"),
    ("system(", "System command execution"),
    ("shell=true", "Unsafe shell parameter"),
    ("sql injection", "SQL injection vulnerability"),
    ("xss", "Cross-site scripting"),
    ("csrf", "CSRF vulnerability without mitigation"),
]

SUSPICIOUS_KEYWORDS = [
    "delete all",
    "drop table",
    "truncate",
    "destroy database",
    "remove all users",
    "unauthorized access",
    "steal data",
    "crack password",
]

SAFE_PRACTICES = [
    "parameterized queries",
    "input sanitization",
    "output encoding",
    "authentication",
    "authorization",
    "encryption",
]


def scan_dangerous_patterns(skill_data: Dict[str, Any]) -> List[ErrorDetail]:
    """Scan for dangerous code patterns."""
    errors = []

    description = skill_data.get("description", "").lower()
    name = skill_data.get("name", "").lower()
    tools = [t.lower() for t in skill_data.get("tools_used", [])]

    combined_text = f"{name} {description}" + " ".join(tools)

    for pattern, risk in DANGEROUS_PATTERNS:
        if pattern in combined_text:
            errors.append(
                ErrorDetail(
                    field="description",
                    rule="SECURITY_RISK",
                    message=f"Security risk detected: {risk}. Unsafe pattern: '{pattern}'",
                    severity="CRITICAL",
                )
            )

    return errors


def scan_suspicious_intent(skill_data: Dict[str, Any]) -> List[ErrorDetail]:
    """Scan for suspicious/malicious intent."""
    errors = []

    description = skill_data.get("description", "").lower()
    name = skill_data.get("name", "").lower()

    combined_text = f"{name} {description}"

    for keyword in SUSPICIOUS_KEYWORDS:
        if keyword in combined_text:
            errors.append(
                ErrorDetail(
                    field="description",
                    rule="MALICIOUS_INTENT",
                    message=f"Suspicious keyword detected: '{keyword}'. Skills must be beneficial.",
                    severity="CRITICAL",
                )
            )

    return errors


def check_safe_practices(skill_data: Dict[str, Any]) -> List[WarningDetail]:
    """Check if high-risk operations mention safety practices."""
    warnings = []

    description = skill_data.get("description", "").lower()

    # High-risk operations
    high_risk_keywords = [
        "database",
        "delete",
        "modify",
        "external api",
        "authentication",
        "user data",
    ]

    is_high_risk = any(keyword in description for keyword in high_risk_keywords)

    if is_high_risk:
        has_safety = any(practice in description for practice in SAFE_PRACTICES)
        if not has_safety:
            warnings.append(
                WarningDetail(
                    field="description",
                    rule="MISSING_SECURITY_MENTION",
                    message="High-risk operation detected. Consider mentioning security practices: parameterized queries, input sanitization, authorization checks.",
                )
            )

    return warnings


def validate_schema_injection_risk(skill_data: Dict[str, Any]) -> List[WarningDetail]:
    """Check for injection risks in schema design."""
    warnings = []

    input_schema = skill_data.get("input_schema", {})
    if not isinstance(input_schema, dict):
        return warnings

    # Check for fields that accept arbitrary input
    dangerous_field_names = ["code", "command", "script", "query", "expression"]

    for field_name in input_schema.keys():
        if any(danger in field_name.lower() for danger in dangerous_field_names):
            warnings.append(
                WarningDetail(
                    field="input_schema",
                    rule="INJECTION_RISK",
                    message=f"Field '{field_name}' could be injection vector. Ensure strict validation and sanitization.",
                )
            )

    return warnings


def run_security_validation(skill_data: Dict[str, Any]) -> tuple[List[ErrorDetail], List[WarningDetail]]:
    """Run all security validations."""
    errors = []
    warnings = []

    errors.extend(scan_dangerous_patterns(skill_data))
    errors.extend(scan_suspicious_intent(skill_data))
    warnings.extend(check_safe_practices(skill_data))
    warnings.extend(validate_schema_injection_risk(skill_data))

    return errors, warnings
