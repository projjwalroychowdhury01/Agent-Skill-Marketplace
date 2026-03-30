#!/usr/bin/env python
"""
Quick Start Script - FastAPI Skill Validator

Run this script to validate a skill without starting the server.
"""

import json
import sys
from typing import Dict, Any

# Import validators
from validators.structural import run_structural_validation
from validators.semantic import run_semantic_validation
from validators.consistency import run_consistency_validation
from validators.security import run_security_validation
from validators.normalization import run_normalization
from validators.scoring import calculate_quality_score
from utils.tag_mapper import map_tags_to_vocabulary

# Import models
from models import ValidationResponse, ErrorDetail


def quick_validate(skill_data: Dict[str, Any]) -> Dict[str, Any]:
    """Quick validation without FastAPI server."""
    
    all_errors = []
    all_warnings = []
    
    print(f"\n🔍 Validating skill: {skill_data.get('name', 'Unknown')}")
    print("=" * 60)
    
    # Step 1-3: Structural
    print("✓ Structural validation...", end="")
    struct_errors = run_structural_validation(skill_data)
    all_errors.extend(struct_errors)
    print(f" ({len(struct_errors)} issues)")
    
    if any(e.severity == "CRITICAL" for e in struct_errors):
        print("❌ CRITICAL ERRORS - Stopping validation")
        return format_results(all_errors, all_warnings, 0)
    
    # Step 4-8: Semantic
    print("✓ Semantic validation...", end="")
    semantic_errors = run_semantic_validation(skill_data)
    all_errors.extend(semantic_errors)
    print(f" ({len(semantic_errors)} issues)")
    
    # Step 9-11: Consistency
    print("✓ Consistency validation...", end="")
    cons_errors, cons_warnings = run_consistency_validation(skill_data)
    all_errors.extend(cons_errors)
    all_warnings.extend(cons_warnings)
    print(f" ({len(cons_errors)} errors, {len(cons_warnings)} warnings)")
    
    # Step 13: Security
    print("✓ Security scan...", end="")
    sec_errors, sec_warnings = run_security_validation(skill_data)
    all_errors.extend(sec_errors)
    all_warnings.extend(sec_warnings)
    print(f" ({len(sec_errors)} errors, {len(sec_warnings)} warnings)")
    
    if sec_errors:
        print("❌ SECURITY ERRORS - Rejecting")
        return format_results(all_errors, all_warnings, 0)
    
    # Normalization
    print("✓ Normalization...", end="")
    normalized_data = run_normalization(skill_data)
    print(" Done")
    
    # Scoring
    print("✓ Quality scoring...", end="")
    score_breakdown, total_score = calculate_quality_score(normalized_data)
    print(f" Score: {total_score}/100")
    
    # Results
    print("\n" + "=" * 60)
    print("📊 VALIDATION RESULTS")
    print("=" * 60)
    
    # Determine status
    critical = [e for e in all_errors if e.severity == "CRITICAL"]
    errors = [e for e in all_errors if e.severity == "ERROR"]
    
    if critical:
        status = "❌ REJECTED"
    elif len(errors) >= 3:
        status = "⚠️  FLAGGED"
    else:
        status = "✅ ACCEPTED"
    
    print(f"\nStatus: {status}")
    print(f"Score: {total_score}/100")
    print(f"Errors: {len(all_errors)} | Warnings: {len(all_warnings)}")
    
    # Score breakdown
    print(f"\n📈 Score Breakdown:")
    print(f"   Description: {score_breakdown.description_quality}/20")
    print(f"   Examples:    {score_breakdown.example_quality}/15")
    print(f"   Tags:        {score_breakdown.tag_quality}/10")
    print(f"   Schema:      {score_breakdown.schema_quality}/10")
    print(f"   Naming:      {score_breakdown.naming_quality}/10")
    print(f"   Consistency: {score_breakdown.consistency_quality}/10")
    
    # Errors and warnings
    if all_errors:
        print(f"\n❌ Errors ({len(all_errors)}):")
        for error in all_errors[:5]:
            print(f"   • {error.field}: {error.message}")
        if len(all_errors) > 5:
            print(f"   ... and {len(all_errors) - 5} more")
    
    if all_warnings:
        print(f"\n⚠️  Warnings ({len(all_warnings)}):")
        for warning in all_warnings[:3]:
            print(f"   • {warning.field}: {warning.message}")
        if len(all_warnings) > 3:
            print(f"   ... and {len(all_warnings) - 3} more")
    
    return {
        "status": status,
        "score": total_score,
        "errors": len(all_errors),
        "warnings": len(all_warnings)
    }


def format_results(errors, warnings, score):
    return {
        "status": "❌ REJECTED" if errors else "✅ ACCEPTED",
        "score": score,
        "errors": len(errors),
        "warnings": len(warnings)
    }


# Example skills
GOOD_SKILL = {
    "name": "JSON Data Extractor",
    "description": "Extracts specified fields from JSON input and generates structured output",
    "category": "data_extraction",
    "tags": ["json", "data extraction", "parsing"],
    "input_schema": {"json_data": "string", "fields": "array"},
    "output_schema": {"extracted": "object", "status": "string"},
    "examples": [{
        "input": {"json_data": '{"name":"John"}', "fields": ["name"]},
        "output": {"extracted": {"name": "John"}, "status": "success"}
    }],
}

BAD_SKILL = {
    "name": "Pass Through",
    "description": "Passes data through",
    "category": "utility",
    "tags": ["pass", "through", "identity"],
    "input_schema": {"data": "string"},
    "output_schema": {"data": "string"},  # IDENTICAL - bad!
}

SECURITY_ISSUE = {
    "name": "Shell Executor",
    "description": "Executes shell commands",
    "category": "utility",
    "tags": ["shell", "execution", "commands"],
    "input_schema": {"command": "string"},
    "output_schema": {"output": "string"},
}


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("⚡ FastAPI Skill Validator - Quick Start")
    print("=" * 60)
    
    if len(sys.argv) > 1:
        # Load from file or stdin
        try:
            if sys.argv[1] == "-":
                skill = json.loads(sys.stdin.read())
            else:
                with open(sys.argv[1]) as f:
                    skill = json.load(f)
            quick_validate(skill)
        except Exception as e:
            print(f"❌ Error: {e}")
            sys.exit(1)
    else:
        # Run examples
        print("\n1️⃣  Testing GOOD skill:")
        quick_validate(GOOD_SKILL)
        
        print("\n\n2️⃣  Testing BAD skill (identical schemas):")
        quick_validate(BAD_SKILL)
        
        print("\n\n3️⃣  Testing SECURITY issue:")
        quick_validate(SECURITY_ISSUE)
        
        print("\n" + "=" * 60)
        print("✨ Use: python quick_start.py <skill.json>")
        print("   Or: cat skill.json | python quick_start.py -")
        print("=" * 60 + "\n")
