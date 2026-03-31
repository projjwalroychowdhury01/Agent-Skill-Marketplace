"""
Duplicate detection utility - finds similar/duplicate skills.
"""

from typing import Dict, List, Optional, Tuple
import hashlib


# In production, this would be a database query
SKILL_DATABASE = {
    # Pre-populated with example skills (in production, load from DB)
}


def calculate_hash(data: Dict) -> str:
    """Calculate hash of skill structure (name, input_schema, output_schema)."""
    # Use name, input keys, and output keys for hash
    structure = {
        "name": (data.get("name") or "").lower(),
        "input_keys": sorted((data.get("input_schema") or {}).keys()),
        "output_keys": sorted((data.get("output_schema") or {}).keys()),
    }

    import json
    hash_str = json.dumps(structure, sort_keys=True)
    return hashlib.md5(hash_str.encode()).hexdigest()


def calculate_similarity(skill1: Dict, skill2: Dict) -> float:
    """Calculate similarity score between two skills (0-1)."""
    name1 = (skill1.get("name") or "").lower()
    name2 = (skill2.get("name") or "").lower()

    # Exact name match
    if name1 == name2:
        return 1.0

    # Partial name match
    if name1 in name2 or name2 in name1:
        overlap = len(set(name1.split()) & set(name2.split()))
        total = len(set(name1.split()) | set(name2.split()))
        name_score = overlap / total if total > 0 else 0
    else:
        name_score = 0

    # Schema similarity
    input1_keys = set((skill1.get("input_schema") or {}).keys())
    input2_keys = set((skill2.get("input_schema") or {}).keys())
    output1_keys = set((skill1.get("output_schema") or {}).keys())
    output2_keys = set((skill2.get("output_schema") or {}).keys())

    input_overlap = len(input1_keys & input2_keys) / len(input1_keys | input2_keys) if len(input1_keys | input2_keys) > 0 else 0
    output_overlap = len(output1_keys & output2_keys) / len(output1_keys | output2_keys) if len(output1_keys | output2_keys) > 0 else 0

    schema_score = (input_overlap + output_overlap) / 2

    # Combined score
    combined_score = (name_score * 0.4) + (schema_score * 0.6)

    return combined_score


def find_duplicates(skill_data: Dict, threshold: float = 0.85) -> List[Tuple[str, float]]:
    """Find potential duplicate skills in database."""
    duplicates = []

    for skill_id, stored_skill in SKILL_DATABASE.items():
        similarity = calculate_similarity(skill_data, stored_skill)

        if similarity >= threshold:
            duplicates.append((skill_id, similarity))

    # Sort by similarity descending
    duplicates.sort(key=lambda x: x[1], reverse=True)

    return duplicates


def is_exact_duplicate(skill_data: Dict) -> Optional[str]:
    """Check if exact duplicate exists."""
    skill_hash = calculate_hash(skill_data)

    # Check hash against database hashes
    for skill_id, stored_skill in SKILL_DATABASE.items():
        if calculate_hash(stored_skill) == skill_hash:
            return skill_id

    return None


def is_likely_duplicate(skill_data: Dict, threshold: float = 0.9) -> Optional[str]:
    """Check if likely duplicate exists (very high similarity)."""
    duplicates = find_duplicates(skill_data, threshold=threshold)

    if duplicates:
        return duplicates[0][0]  # Return highest similarity

    return None


def check_near_duplicates(skill_data: Dict, threshold: float = 0.75) -> List[Dict]:
    """Find near-duplicates that should be reviewed."""
    near_dupes = []

    duplicates = find_duplicates(skill_data, threshold=threshold)

    for skill_id, similarity in duplicates:
        if skill_id in SKILL_DATABASE:
            near_dupes.append({
                "id": skill_id,
                "name": SKILL_DATABASE[skill_id].get("name"),
                "similarity": similarity,
            })

    return near_dupes


def add_skill_to_database(skill_id: str, skill_data: Dict) -> None:
    """Add skill to the database (for testing)."""
    SKILL_DATABASE[skill_id] = skill_data


def clear_database() -> None:
    """Clear database (for testing)."""
    SKILL_DATABASE.clear()
