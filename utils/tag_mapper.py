"""
Tag mapping utility - maps tags to controlled vocabulary.
"""

from typing import Dict, List, Tuple


CONTROLLED_VOCABULARY = {
    # Data Operations
    "data extraction": ["extraction", "scraping", "data extraction", "extract data"],
    "data transformation": ["transformation", "transform", "convert data", "data conversion"],
    "data validation": ["validation", "validate", "check data", "data validation"],
    "data aggregation": ["aggregation", "aggregate", "combine data", "merging"],

    # Text & NLP
    "text processing": ["text", "nlp", "language", "text processing", "natural language"],
    "text generation": ["generation", "generate text", "text generation", "produce text"],
    "text classification": ["classification", "classify text", "text classification"],
    "sentiment analysis": ["sentiment", "emotion", "sentiment analysis"],

    # Image & Vision
    "image processing": ["image", "vision", "image processing", "visual", "cv"],
    "image generation": ["image generation", "generate image", "image synthesis"],
    "object detection": ["detection", "detect objects", "object detection"],

    # API & Integration
    "api integration": ["api", "rest", "http", "api integration", "web service"],
    "database operations": ["database", "db", "sql", "database operations", "query"],
    "authentication": ["auth", "authentication", "security", "login", "credentials"],

    # ML & AI
    "machine learning": ["ml", "machine learning", "model", "training", "prediction"],
    "prediction": ["prediction", "predict", "forecasting", "inference"],
    "classification": ["classification", "classify", "categorize", "label"],

    # Utility
    "parsing": ["parsing", "parse", "extract", "parse data"],
    "formatting": ["formatting", "format", "arrange", "structure"],
    "filtering": ["filtering", "filter", "select", "search"],
    "sorting": ["sorting", "sort", "order", "arrange"],
    "mapping": ["mapping", "map", "transform", "remap"],
    "encoding": ["encoding", "encode", "compress", "serialize"],
    "decoding": ["decoding", "decode", "decompress", "deserialize"],
}


def find_closest_match(tag: str, vocabulary: Dict[str, List[str]]) -> Tuple[str, float]:
    """Find closest matching controlled tag for a given tag."""
    tag_lower = tag.lower().strip()

    # Exact match
    for controlled, synonyms in vocabulary.items():
        if tag_lower in synonyms or tag_lower == controlled.lower():
            return controlled, 1.0

    # Substring match
    best_match = None
    best_score = 0.0

    for controlled, synonyms in vocabulary.items():
        for synonym in synonyms:
            if tag_lower in synonym or synonym in tag_lower:
                score = len(set(tag_lower.split()) & set(synonym.split())) / len(set(tag_lower.split()) | set(synonym.split()))
                if score > best_score:
                    best_score = score
                    best_match = controlled

    if best_match:
        return best_match, best_score

    return tag, 0.0


def map_tags_to_vocabulary(tags: List[str]) -> Tuple[List[str], Dict[str, str]]:
    """Map tags to controlled vocabulary. Returns normalized tags and suggestions."""
    normalized_tags = []
    suggestions = {}

    for tag in tags:
        controlled_tag, confidence = find_closest_match(tag, CONTROLLED_VOCABULARY)

        if confidence >= 0.5 and confidence < 1.0:
            # Suggest but don't force
            suggestions[tag] = controlled_tag
            normalized_tags.append(tag)  # Keep original, user should approve
        else:
            # Use controlled tag if high confidence
            normalized_tags.append(controlled_tag)

    # Deduplicate
    normalized_tags = list(dict.fromkeys(normalized_tags))

    return normalized_tags, suggestions


def is_tag_in_vocabulary(tag: str) -> bool:
    """Check if tag exists in controlled vocabulary."""
    tag_lower = tag.lower().strip()

    for controlled, synonyms in CONTROLLED_VOCABULARY.items():
        if tag_lower in synonyms or tag_lower == controlled.lower():
            return True

    return False


def get_all_controlled_tags() -> List[str]:
    """Return all controlled tags."""
    return list(CONTROLLED_VOCABULARY.keys())
