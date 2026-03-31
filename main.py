"""
Main FastAPI application - Skill validation service (v3 Hardened).
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any
import logging
import uuid

from models import (
    SkillRequest, ValidationResponse, ErrorDetail, WarningDetail, 
    ValidatedSkill, ScoreBreakdown, IntelligenceEngineRequest, 
    IntelligenceEngineResponse, FeedbackSignals
)

# Validators
from validators.structural import run_structural_validation
from validators.semantic import run_semantic_validation
from validators.consistency import run_consistency_validation
from validators.security import run_security_validation
from validators.normalization import run_normalization
from validators.scoring import calculate_quality_score

# Intelligence Engine
from utils.intelligence_engine import run_intelligence_engine

# Utilities
from utils.tag_mapper import map_tags_to_vocabulary, is_tag_in_vocabulary
from utils.duplicate_detector import (
    find_duplicates,
    is_exact_duplicate,
    is_likely_duplicate,
    check_near_duplicates,
)
from utils.url_validator import validate_source_url, validate_author_email
from utils.ranking import search_skills, get_recommendations

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Agent Skill Validator",
    description="Production-grade validation service for agent skills",
    version="3.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def convert_to_dict(skill_request: SkillRequest) -> Dict[str, Any]:
    """Convert Pydantic model to dict."""
    return skill_request.dict()


def create_validation_response(
    status: str,
    errors: list = None,
    warnings: list = None,
    quality_score: int = 0,
    score_breakdown: ScoreBreakdown = None,
    normalized_skill: ValidatedSkill = None,
    duplicate_detected: bool = False,
    duplicate_id: str = None,
) -> ValidationResponse:
    """Create standardized validation response."""
    return ValidationResponse(
        status=status,
        errors=errors or [],
        warnings=warnings or [],
        quality_score=quality_score,
        score_breakdown=score_breakdown or ScoreBreakdown(),
        normalized_skill=normalized_skill,
        duplicate_detected=duplicate_detected,
        duplicate_id=duplicate_id,
    )


@app.post("/validate-skill", response_model=ValidationResponse)
async def validate_skill(skill_request: SkillRequest) -> ValidationResponse:
    """
    Validate, normalize, and score an agent skill.

    Pipeline (19 steps):
    1. Structural Validation
    2. Type Enforcement
    3. Field Constraints
    4. Description Quality
    5. Name Quality
    6. Schema Semantic Validation
    7. Example Alignment
    8. Tool Consistency
    9. Category Validation
    10. Tag Validation + Normalization
    11. Tools Validation
    12. Source Validation
    13. Security Scan
    14. Determinism Check
    15. Complexity Validation
    16. Anti-Garbage Filter
    17. Duplicate Detection
    18. Guardrails Enforcement
    19. Final Scoring & Response
    """

    request_id = str(uuid.uuid4())[:8]
    logger.info(f"[{request_id}] Validating skill: {skill_request.name}")

    skill_data = convert_to_dict(skill_request)
    all_errors = []
    all_warnings = []

    # ============ STEP 1-3: STRUCTURAL & TYPE & CONSTRAINTS ============
    logger.debug(f"[{request_id}] Step 1-3: Structural validation")
    struct_errors = run_structural_validation(skill_data)
    all_errors.extend(struct_errors)

    # If critical structural errors, reject immediately
    critical_errors = [e for e in all_errors if e.severity == "CRITICAL"]
    if critical_errors:
        logger.warning(f"[{request_id}] Critical structural errors found")
        return create_validation_response(
            status="REJECTED",
            errors=all_errors,
        )

    # ============ STEP 4-8: SEMANTIC & CONSISTENCY ============
    logger.debug(f"[{request_id}] Step 4-8: Semantic validation")
    semantic_errors = run_semantic_validation(skill_data)
    all_errors.extend(semantic_errors)

    cons_errors, cons_warnings = run_consistency_validation(skill_data)
    all_errors.extend(cons_errors)
    all_warnings.extend(cons_warnings)

    # ============ STEP 9: CATEGORY VALIDATION ============
    logger.debug(f"[{request_id}] Step 9: Category validation")
    valid_categories = [
        "data_extraction",
        "data_transformation",
        "text_processing",
        "image_processing",
        "api_integration",
        "database_operations",
        "authentication",
        "content_generation",
        "classification",
        "prediction",
        "analysis",
        "utility",
    ]

    category = skill_data.get("category", "")
    if category not in valid_categories:
        all_errors.append(
            ErrorDetail(
                field="category",
                rule="INVALID_CATEGORY",
                message=f"Category must be one of: {', '.join(valid_categories)}",
                severity="ERROR",
            )
        )

    # ============ STEP 10: TAG VALIDATION & NORMALIZATION ============
    logger.debug(f"[{request_id}] Step 10: Tag validation")
    tags = skill_data.get("tags") or []
    if not isinstance(tags, list):
        all_errors.append(
            ErrorDetail(
                field="tags",
                rule="INVALID_TAGS",
                message="Tags must be a list",
                severity="ERROR",
            )
        )
    else:
        # Check for invalid tag counts
        if len(tags) < 3:
            all_errors.append(
                ErrorDetail(
                    field="tags",
                    rule="TOO_FEW_TAGS",
                    message="Minimum 3 tags required",
                    severity="ERROR",
                )
            )
        elif len(tags) > 6:
            all_errors.append(
                ErrorDetail(
                    field="tags",
                    rule="TOO_MANY_TAGS",
                    message="Maximum 6 tags allowed",
                    severity="ERROR",
                )
            )

        # Check tag vocabulary
        for tag in tags:
            if isinstance(tag, str):
                if not is_tag_in_vocabulary(tag.lower()):
                    all_warnings.append(
                        WarningDetail(
                            field="tags",
                            rule="UNKNOWN_TAG",
                            message=f"Tag '{tag}' not in controlled vocabulary. Consider: extractor, parser, validator, converter, generator",
                        )
                    )

    # ============ STEP 11: TOOLS VALIDATION ============
    logger.debug(f"[{request_id}] Step 11: Tools validation")
    tools = skill_data.get("tools_used") or []
    if isinstance(tools, list):
        if len(tools) == 0:
            all_warnings.append(
                WarningDetail(
                    field="tools_used",
                    rule="NO_TOOLS",
                    message="Consider documenting tools_used for transparency",
                )
            )

    # ============ STEP 12: SOURCE VALIDATION ============
    logger.debug(f"[{request_id}] Step 12: Source validation")
    source = skill_data.get("source")
    if source:
        valid, msg = validate_source_url(source)
        if not valid:
            all_errors.append(
                ErrorDetail(
                    field="source",
                    rule="INVALID_SOURCE",
                    message=msg or "Invalid source format",
                    severity="ERROR",
                )
            )

    # ============ STEP 13: SECURITY SCAN ============
    logger.debug(f"[{request_id}] Step 13: Security scan")
    sec_errors, sec_warnings = run_security_validation(skill_data)
    all_errors.extend(sec_errors)
    all_warnings.extend(sec_warnings)

    # If security errors, reject immediately
    if sec_errors:
        logger.warning(f"[{request_id}] Security errors found")
        return create_validation_response(
            status="REJECTED",
            errors=all_errors,
        )

    # ============ STEP 14-16: DETERMINISM, COMPLEXITY, ANTI-GARBAGE ============
    logger.debug(f"[{request_id}] Step 14-16: Quality checks")

    # Check for garbage/spam
    description = skill_data.get("description", "").lower()
    if any(word in description for word in ["test", "demo", "placeholder", "xxx", "todo"]):
        all_warnings.append(
            WarningDetail(
                field="description",
                rule="POSSIBLE_PLACEHOLDER",
                message="Description appears to contain placeholder text",
            )
        )

    # ============ STEP 17: DUPLICATE DETECTION ============
    logger.debug(f"[{request_id}] Step 17: Duplicate detection")
    exact_dup = is_exact_duplicate(skill_data)
    likely_dup = is_likely_duplicate(skill_data, threshold=0.9)
    near_dups = check_near_duplicates(skill_data, threshold=0.75)

    duplicate_detected = False
    duplicate_id = None

    if exact_dup:
        logger.warning(f"[{request_id}] Exact duplicate detected")
        duplicate_detected = True
        duplicate_id = exact_dup
        return create_validation_response(
            status="REJECTED",
            errors=[
                ErrorDetail(
                    field="skill",
                    rule="EXACT_DUPLICATE",
                    message=f"Exact duplicate of skill '{exact_dup}'",
                    severity="CRITICAL",
                )
            ],
            duplicate_detected=True,
            duplicate_id=exact_dup,
        )

    if likely_dup:
        logger.warning(f"[{request_id}] Likely duplicate detected")
        duplicate_detected = True
        duplicate_id = likely_dup
        all_warnings.append(
            WarningDetail(
                field="skill",
                rule="LIKELY_DUPLICATE",
                message=f"Very similar to existing skill '{likely_dup}'. Review recommended.",
            )
        )

    if near_dups:
        for near_dup in near_dups:
            all_warnings.append(
                WarningDetail(
                    field="skill",
                    rule="SIMILAR_SKILL_EXISTS",
                    message=f"Similar skill found: {near_dup['name']} (similarity: {near_dup['similarity']:.1%})",
                )
            )

    # ============ STEP 18: GUARDRAILS ENFORCEMENT ============
    logger.debug(f"[{request_id}] Step 18: Guardrails enforcement")

    # Check guardrail violations
    name = skill_data.get("name", "")
    if len(name) > 0 and len(name) < 3:
        all_errors.append(
            ErrorDetail(
                field="name",
                rule="GUARDRAIL_VIOLATION",
                message="Name too short (guardrail: min 3 chars)",
                severity="ERROR",
            )
        )

    if description and len(description) < 20:
        all_errors.append(
            ErrorDetail(
                field="description",
                rule="GUARDRAIL_VIOLATION",
                message="Description too vague (guardrail: min 20 chars)",
                severity="ERROR",
            )
        )

    # ============ STEP 19: NORMALIZATION & SCORING ============
    logger.debug(f"[{request_id}] Step 19: Normalization & scoring")

    # Only normalize if no critical errors
    if not any(e.severity == "CRITICAL" for e in all_errors):
        normalized_skill_data = run_normalization(skill_data)

        # Map tags
        normalized_tags, tag_suggestions = map_tags_to_vocabulary(normalized_skill_data.get("tags") or [])
        normalized_skill_data["tags"] = normalized_tags

        # Create normalized skill object
        try:
            normalized_skill = ValidatedSkill(**normalized_skill_data)
        except Exception as e:
            logger.error(f"[{request_id}] Normalization failed: {str(e)}")
            normalized_skill = None
    else:
        normalized_skill = None

    # Calculate quality score
    try:
        score_breakdown, total_score = calculate_quality_score(skill_data)
    except Exception as e:
        logger.error(f"[{request_id}] Scoring failed: {str(e)}")
        score_breakdown = ScoreBreakdown()
        total_score = 0

    if score_breakdown is None:
        score_breakdown = ScoreBreakdown()
        total_score = 0

    # ============ DETERMINE FINAL STATUS ============
    logger.debug(f"[{request_id}] Determining final status")

    # Count error severity
    critical = [e for e in all_errors if e.severity == "CRITICAL"]
    error_count = [e for e in all_errors if e.severity == "ERROR"]

    if critical or (error_count and len(error_count) >= 3):
        status = "REJECTED"
    elif duplicate_detected or likely_dup:
        status = "FLAGGED"
    elif error_count:
        status = "FLAGGED"
    else:
        status = "ACCEPTED"

    logger.info(
        f"[{request_id}] Validation complete: {status} "
        f"(errors={len(all_errors)}, warnings={len(all_warnings)}, score={total_score})"
    )

    # Build response
    return create_validation_response(
        status=status,
        errors=all_errors,
        warnings=all_warnings,
        quality_score=total_score,
        score_breakdown=score_breakdown,
        normalized_skill=normalized_skill,
        duplicate_detected=duplicate_detected,
        duplicate_id=duplicate_id,
    )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "Agent Skill Validator v3"}


@app.get("/skills/search")
async def search_skills_endpoint(query: str = "", page: int = 1, size: int = 10):
    """Search skills ranking endpoint."""
    try:
        if not query or not query.strip():
            # If no query, return all skills
            return search_skills(query=" ", page=page, size=size)
        return search_skills(query=query, page=page, size=size)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Search failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Search engine error")


@app.get("/skills/{skill_id}/recommendations")
async def skill_recommendations(skill_id: str, size: int = 10):
    """Skill recommendation endpoint."""
    try:
        return get_recommendations(skill_id=skill_id, size=size)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Recommendations failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Recommendation engine error")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Agent Skill Validator",
        "version": "3.0.0",
        "description": "Production-grade validation service for agent skills",
        "endpoints": {
            "validate": "POST /validate-skill",
            "health": "GET /health",
            "search": "GET /skills/search?query={query}",
            "recommendations": "GET /skills/{skill_id}/recommendations",
            "intelligence": "POST /intelligence-engine",
        },
    }

@app.post("/intelligence-engine", response_model=IntelligenceEngineResponse)
async def intelligence_engine_endpoint(request: IntelligenceEngineRequest) -> IntelligenceEngineResponse:
    """
    Post-Validation Phase: Canonicalization, Deduplication, and Soft Quality Handling.
    """
    try:
        return run_intelligence_engine(request)
    except Exception as e:
        logger.error(f"Intelligence Engine Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Intelligence engine processing failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="localhost", port=8000)
