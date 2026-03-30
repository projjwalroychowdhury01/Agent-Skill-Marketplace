"""
Pydantic models for skill validation.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, validator


class SkillRequest(BaseModel):
    """Incoming skill submission."""
    name: str
    description: str
    category: str
    tags: List[str]
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    examples: List[Dict[str, Any]] = []
    tools_used: List[str] = []
    source: Optional[str] = None
    author: Optional[str] = None

    class Config:
        extra = "allow"  # Allow extra fields but flag them


class ValidatedSkill(BaseModel):
    """Normalized validated skill."""
    name: str
    description: str
    category: str
    tags: List[str]
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    examples: List[Dict[str, Any]]
    tools_used: List[str]
    source: Optional[str] = None
    author: Optional[str] = None


class ErrorDetail(BaseModel):
    """Single validation error."""
    field: str
    rule: str
    message: str
    severity: str  # "CRITICAL", "ERROR", "WARNING"


class WarningDetail(BaseModel):
    """Single validation warning."""
    field: str
    rule: str
    message: str


class ScoreBreakdown(BaseModel):
    """Quality score components."""
    description_quality: int = 0
    example_quality: int = 0
    tag_quality: int = 0
    schema_quality: int = 0
    naming_quality: int = 0
    consistency_quality: int = 0
    total: int = 0


class ValidationResponse(BaseModel):
    """API response for validation."""
    status: str  # "ACCEPTED", "REJECTED", "FLAGGED"
    errors: List[ErrorDetail] = []
    warnings: List[WarningDetail] = []
    quality_score: int = 0
    score_breakdown: ScoreBreakdown = Field(default_factory=ScoreBreakdown)
    normalized_skill: Optional[ValidatedSkill] = None
    duplicate_detected: bool = False
    duplicate_id: Optional[str] = None
