"""
In-memory skill catalog for ranking and recommendation.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional

SKILL_INDEX: List[Dict] = [
    {
        "id": "skill-001",
        "name": "JSON Data Extractor",
        "creator_id": "user_1",
        "category": "data_extraction",
        "description": "Extracts specified fields from JSON input and returns structured output",
        "tags": ["json", "data extraction", "parsing"],
        "created_at": datetime.utcnow() - timedelta(days=10),
        "usage_count": 120,
        "verified_usage": 90,
        "saves": 45,
        "weighted_ratings": 85,
        "quality_score": 85,
        "freshness_score": 0,
        "completeness_score": 90,
        "relevance_score": 70,
        "popularity_score": 0,
    },
    {
        "id": "skill-002",
        "name": "CSV to JSON Converter",
        "creator_id": "user_2",
        "category": "data_transformation",
        "description": "Converts CSV data to structured JSON format",
        "tags": ["csv", "json", "conversion"],
        "created_at": datetime.utcnow() - timedelta(days=40),
        "usage_count": 350,
        "verified_usage": 280,
        "saves": 80,
        "weighted_ratings": 210,
        "quality_score": 78,
        "freshness_score": 0,
        "completeness_score": 83,
        "relevance_score": 68,
        "popularity_score": 0,
    },
    {
        "id": "skill-003",
        "name": "Text Validator",
        "creator_id": "user_1",
        "category": "data_validation",
        "description": "Validates input text against rules",
        "tags": ["text", "validation", "encoding"],
        "created_at": datetime.utcnow() - timedelta(days=3),
        "usage_count": 20,
        "verified_usage": 15,
        "saves": 5,
        "weighted_ratings": 10,
        "quality_score": 65,
        "freshness_score": 0,
        "completeness_score": 70,
        "relevance_score": 55,
        "popularity_score": 0,
    },
    {
        "id": "skill-004",
        "name": "API Response Parser",
        "creator_id": "user_3",
        "category": "api_integration",
        "description": "Parses and normalizes API JSON responses",
        "tags": ["api", "parsing", "normalization"],
        "created_at": datetime.utcnow() - timedelta(days=2),
        "usage_count": 5,
        "verified_usage": 4,
        "saves": 2,
        "weighted_ratings": 3,
        "quality_score": 58,
        "freshness_score": 0,
        "completeness_score": 60,
        "relevance_score": 50,
        "popularity_score": 0,
    },
]


def get_skill_by_id(skill_id: str) -> Optional[Dict]:
    for skill in SKILL_INDEX:
        if skill["id"] == skill_id:
            return skill
    return None


def get_all_skills() -> List[Dict]:
    return SKILL_INDEX


def add_skill(item: Dict) -> None:
    SKILL_INDEX.append(item)


def update_skill(skill_id: str, updates: Dict) -> None:
    skill = get_skill_by_id(skill_id)
    if skill:
        skill.update(updates)
