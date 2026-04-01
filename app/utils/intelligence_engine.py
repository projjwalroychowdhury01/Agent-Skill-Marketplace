"""
Intelligence Engine Utility for Skill Marketplace.
Implements the post-validation (v1 Production) specification.
"""

from typing import Dict, Any, List, Tuple
from models import IntelligenceEngineRequest, IntelligenceEngineResponse, FeedbackSignals
from utils.duplicate_detector import calculate_similarity

def _generate_canonical_name(name: str) -> str:
    """Generate precise, descriptive, standardized name."""
    # Standard Title Case, remove generic words like "tool", "script"
    if not name:
        return "Unknown Skill"
    
    words = name.split()
    clean_words = [w for w in words if w.lower() not in ("tool", "script", "bot", "agent")]
    canonical = " ".join(clean_words).title()
    
    # Just in case it's completely empty after cleaning
    if not canonical:
        return name.title()
    return canonical

def _calculate_schema_clarity(skill: Dict[str, Any]) -> int:
    """Calculate 0-100 score for schema clarity."""
    input_keys = len(skill.get("input_schema", {}).keys())
    output_keys = len(skill.get("output_schema", {}).keys())
    total_keys = input_keys + output_keys
    
    if total_keys >= 4:
        return 100
    elif total_keys > 0:
        return 50 + (total_keys * 10)
    return 30

def _calculate_description_specificity(desc: str) -> int:
    """Calculate 0-100 score for description specificity."""
    if not desc:
        return 0
    words = len(desc.split())
    if words >= 15:
        return 100
    return int((words / 15.0) * 100)

def match_existing_skills(validated_skill: Dict[str, Any], existing_skills: List[Dict[str, Any]]) -> Tuple[float, str, str]:
    """Find the highest similarity match in existing skills."""
    best_sim = 0.0
    best_id = ""
    best_name = ""
    v_cat = validated_skill.get("category", "").lower()
    
    for existing in existing_skills:
        # Anti-pollution rule: Reject merging if different core function (category)
        e_cat = existing.get("category", "").lower()
        if v_cat and e_cat and v_cat != e_cat:
            continue
            
        sim = calculate_similarity(validated_skill, existing)
        if sim > best_sim:
            best_sim = sim
            best_id = existing.get("id", str(hash(existing.get("name", ""))))
            best_name = existing.get("name", "")
            
    return best_sim, best_id, best_name

def run_intelligence_engine(request: IntelligenceEngineRequest) -> IntelligenceEngineResponse:
    """Run the intelligence engine logic on a validated skill."""
    skill = request.validated_skill
    existing = request.existing_skills
    feedback = request.feedback_signals or FeedbackSignals()
    quality_score = skill.get("quality_score", 100)  # assume 100 if missing initially, but usually set
    
    status = "NEW"
    action = "STORE"
    reasoning_parts = []
    
    canonical_skill_id = ""
    similarity_score, best_match_id, best_match_name = match_existing_skills(skill, existing)
    
    # 1. CANONICALIZATION
    if similarity_score > 0.85:
        status = "MERGED"
        action = "MERGE"
        canonical_skill_id = best_match_id
        reasoning_parts.append(f"Strong duplicate mapped to {best_match_name} (sim: {similarity_score:.2f}).")
    elif similarity_score >= 0.65:
        # FLAG as potential merge
        status = "NEW"
        action = "STORE"
        reasoning_parts.append(f"Potential merge flagged with {best_match_name} (sim: {similarity_score:.2f}).")
    else:
        reasoning_parts.append("No strong duplicates found. Treated as new entity.")

    # 4. SOFT QUALITY HANDLING
    if quality_score < 60:
        status = "LOW_QUALITY"
        action = "DOWNRANK"
        reasoning_parts.append(f"Soft quality handling triggered (score: {quality_score} < 60).")

    # 2 & 7. CANONICAL NAME GENERATION & NORMALIZATION
    canonical_name = _generate_canonical_name(skill.get("name", ""))
    skill["name"] = canonical_name
    # Tag cleanup assumes `run_normalization` already happened, but we can enforce lowercasing
    skill["tags"] = [t.lower() for t in skill.get("tags", [])]

    # 5. FEEDBACK INTEGRATION
    ranking_score = float((quality_score * 0.5) + (feedback.click_rate * 20.0) + (feedback.usage_count * 15.0) + (feedback.user_rating * 15.0))
    
    # 6. CONFIDENCE SCORE
    schema_clarity = _calculate_schema_clarity(skill)
    desc_specificity = _calculate_description_specificity(skill.get("description", ""))
    
    sim_conf = 100.0 if similarity_score > 0.85 else (similarity_score * 100) if similarity_score else 80.0
    # Penalty if flagged (0.65 - 0.85) to ensure confidence < 70
    if 0.65 <= similarity_score <= 0.85:
        sim_conf = 60.0
        
    confidence_score = (sim_conf + schema_clarity + desc_specificity) / 3.0

    return IntelligenceEngineResponse(
        status=status,
        canonical_skill_id=canonical_skill_id,
        canonical_name=canonical_name,
        similarity_score=similarity_score,
        action=action,
        normalized_skill=skill,
        ranking_score=ranking_score,
        confidence_score=confidence_score,
        reasoning=" | ".join(reasoning_parts)
    )
