"""
Ranking and recommendation helper module.
"""

from datetime import datetime, timedelta
from functools import lru_cache
from math import log
from typing import Dict, List, Optional, Tuple

from config import (
    ANTI_SPAM_SETTINGS,
    CACHE_SETTINGS,
    DIVERSITY_SETTINGS,
    EXPLORATION_SETTINGS,
    RANKING_THRESHOLDS,
    RANKING_WEIGHTS,
)
from utils.skill_catalog import get_all_skills, get_skill_by_id

STOPWORDS = {
    "a",
    "an",
    "the",
    "and",
    "or",
    "in",
    "on",
    "for",
    "to",
    "with",
    "by",
    "of",
    "is",
    "as",
    "at",
    "from",
    "it",
    "this",
    "that",
}

SYNONYM_MAP = {
    "scrape": "web-scraping",
    "scraper": "web-scraping",
    "etl": "data extraction",
    "transform": "data transformation",
    "parser": "parsing",
}

# Simple query caching with expiration
# _query_cache: Dict[str, Dict] = {}


def sanitize_query(query: str) -> str:
    if not isinstance(query, str):
        raise ValueError("Query must be a string")

    query = query.strip()
    if len(query) == 0 or len(query) > RANKING_THRESHOLDS["max_query_length"]:
        raise ValueError("Query length must be between 1 and 200 characters")

    # Basic sanitize (no injections): reject suspicious punctuation sequences
    if "--" in query or ";" in query or "/*" in query or "*/" in query:
        raise ValueError("Query contains invalid characters")

    return query


def preprocess_query(query: str) -> List[str]:
    query = query.lower()
    tokens = [tok.strip() for tok in query.split() if tok.strip()]
    processed = []

    for tok in tokens:
        if tok in STOPWORDS:
            continue

        if tok in SYNONYM_MAP:
            tok = SYNONYM_MAP[tok]

        # basic stemming (remove common suffixes)
        for suffix in ["ing", "ed", "s"]:
            if tok.endswith(suffix) and len(tok) > len(suffix) + 2:
                tok = tok[: -len(suffix)]
                break

        processed.append(tok)

    return processed


def detect_keyword_stuffing(query_tokens: List[str]) -> float:
    if not query_tokens:
        return 0.0

    counts: Dict[str, int] = {}
    for tok in query_tokens:
        counts[tok] = counts.get(tok, 0) + 1

    max_repeat = max(counts.values())
    ratio = max_repeat / len(query_tokens)
    return ratio


def calculate_trust_weighted_popularity(skill: Dict) -> float:
    verified = float(skill.get("verified_usage", 0))
    saves = float(skill.get("saves", 0))
    ratings = float(skill.get("weighted_ratings", 0))
    raw = float(skill.get("usage_count", 0))

    # apply unverified penalty
    unverified = max(0.0, raw - verified)
    penalty = unverified * 0.2

    score = log(1.0 + verified + saves + ratings) - penalty
    return max(score, 0.0)


def calculate_freshness(skill: Dict) -> float:
    created = skill.get("created_at")
    if not isinstance(created, datetime):
        return 0.0
    age_days = (datetime.utcnow() - created).days
    freshness = max(0.0, 100.0 - age_days)
    return freshness


def calculate_exploration(skill: Dict) -> float:
    usage = skill.get("usage_count", 0)
    threshold = EXPLORATION_SETTINGS["cold_start_threshold"]
    if usage < threshold:
        boost = (threshold - usage) / threshold * EXPLORATION_SETTINGS["boost_factor"]
        decay = min(1.0, (datetime.utcnow() - skill.get("created_at", datetime.utcnow())).days / EXPLORATION_SETTINGS["decay_days"])
        return max(0.0, boost * (1 - decay))
    return 0.0


def min_max_normalize(values: List[float]) -> List[float]:
    if not values:
        return []

    v_min = min(values)
    v_max = max(values)
    if v_max == v_min:
        return [100.0 for _ in values]

    normalized = [max(0.0, min(100.0, (v - v_min) / (v_max - v_min) * 100.0)) for v in values]
    return normalized


def compute_scores(candidates: List[Dict], query_tokens: List[str]) -> List[Dict]:
    for skill in candidates:
        text = f"{skill.get('name')} {skill.get('description')} {' '.join(skill.get('tags', []))}".lower()
        keyword_hits = sum(1 for token in query_tokens if token in text)
        relevance = 100.0 * keyword_hits / (len(query_tokens) if query_tokens else 1)

        skill["relevance_score"] = min(100.0, relevance)
        skill["popularity_score"] = calculate_trust_weighted_popularity(skill)
        skill["freshness_score"] = calculate_freshness(skill)
        skill["completeness_score"] = float(skill.get("completeness_score", 0))
        skill["exploration_score"] = calculate_exploration(skill)

    # component lists
    rels = [s["relevance_score"] for s in candidates]
    quals = [s.get("quality_score", 0.0) for s in candidates]
    pops = [s["popularity_score"] for s in candidates]
    fresh = [s["freshness_score"] for s in candidates]
    compl = [s["completeness_score"] for s in candidates]
    expo = [s["exploration_score"] for s in candidates]

    norm_rels = min_max_normalize(rels)
    norm_quals = min_max_normalize(quals)
    norm_pops = min_max_normalize(pops)
    norm_fresh = min_max_normalize(fresh)
    norm_compl = min_max_normalize(compl)
    norm_expo = min_max_normalize(expo)

    ranked = []

    for idx, skill in enumerate(candidates):
        final = (
            RANKING_WEIGHTS["relevance"] * norm_rels[idx]
            + RANKING_WEIGHTS["quality"] * norm_quals[idx]
            + RANKING_WEIGHTS["popularity"] * norm_pops[idx]
            + RANKING_WEIGHTS["freshness"] * norm_fresh[idx]
            + RANKING_WEIGHTS["completeness"] * norm_compl[idx]
            + RANKING_WEIGHTS["exploration"] * norm_expo[idx]
        )

        skill["normalized_scores"] = {
            "relevance": norm_rels[idx],
            "quality": norm_quals[idx],
            "popularity": norm_pops[idx],
            "freshness": norm_fresh[idx],
            "completeness": norm_compl[idx],
            "exploration": norm_expo[idx],
        }

        skill["final_score"] = final
        ranked.append(skill)

    ranked.sort(key=lambda x: x["final_score"], reverse=True)
    return ranked


def apply_filters(candidates: List[Dict]) -> List[Dict]:
    out = []
    for skill in candidates:
        if skill.get("relevance_score", 0.0) < RANKING_THRESHOLDS["min_relevance"]:
            continue
        if skill.get("quality_score", 0.0) < RANKING_THRESHOLDS["min_quality"]:
            continue
        out.append(skill)
    return out


def enforce_diversity(ranked: List[Dict], limit: int) -> List[Dict]:
    by_creator = {}
    final = []
    category_seen = set()

    for skill in ranked:
        creator = skill.get("creator_id")
        if creator is None:
            continue

        count = by_creator.get(creator, 0)
        if count >= DIVERSITY_SETTINGS["max_per_creator"]:
            continue

        by_creator[creator] = count + 1
        final.append(skill)

        if len(final) >= limit:
            break

    # Ensure category diversity in top chunk
    if final:
        categories = set(s.get("category") for s in final if s.get("category"))
        if len(categories) / max(1, len(final)) < DIVERSITY_SETTINGS["required_category_frac"]:
            # fallback to top quality from broader index, respecting max creator
            extra = [s for s in ranked if s not in final]
            for s in extra:
                if len(final) >= limit:
                    break
                if s.get("category") not in categories:
                    final.append(s)
                    categories.add(s.get("category"))

    return final[:limit]


def near_duplicate(skill_a: Dict, skill_b: Dict) -> bool:
    if skill_a["id"] == skill_b["id"]:
        return True
    if skill_a.get("creator_id") == skill_b.get("creator_id") and skill_a.get("category") == skill_b.get("category"):
        common_tags = set(skill_a.get("tags", [])) & set(skill_b.get("tags", []))
        return len(common_tags) >= 2
    return False


def get_fallback_results(size: int = 10) -> List[Dict]:
    skills = get_all_skills()
    skills_sorted = sorted(skills, key=lambda x: x.get("quality_score", 0), reverse=True)
    if not skills_sorted:
        return []
    return skills_sorted[:size]


# def cache_set(query: str, value: Dict):
#     _query_cache[query] = {
#         "value": value,
#         "expires": datetime.utcnow() + timedelta(seconds=CACHE_SETTINGS["result_ttl_seconds"]),
#     }


# def cache_get(query: str) -> Optional[Dict]:
#     entry = _query_cache.get(query)
#     if not entry:
#         return None

#     if entry["expires"] < datetime.utcnow():
#         del _query_cache[query]
#         return None

#     return entry["value"]


def search_skills(query: str, page: int = 1, size: int = 10) -> Dict:
    sanitized = sanitize_query(query)
    tokens = preprocess_query(sanitized)

    # Anti-spam
    ratio = detect_keyword_stuffing(tokens)
    if ratio > ANTI_SPAM_SETTINGS["max_repeated_token_ratio"]:
        raise ValueError("Query appears to be spam or keyword stuffing")

    cache_key = f"search:{sanitized}:{page}:{size}"
    cached = cache_get(cache_key)
    if cached is not None:
        return cached

    candidates = get_all_skills()

    computed = compute_scores(candidates, tokens)
    filtered = apply_filters(computed)

    if not filtered:
        fallback = get_fallback_results(size)
        response = {
            "query": sanitized,
            "page": page,
            "size": size,
            "results": fallback,
            "explain": "Fallback to top-quality skills",
        }
        cache_set(cache_key, response)
        return response

    top = enforce_diversity(filtered, limit=size * page)
    start = (page - 1) * size
    end = start + size
    paginated = top[start:end]

    explain_data = {
        skill["id"]: {
            "scores": skill.get("normalized_scores", {}),
            "weights": RANKING_WEIGHTS,
            "final_score": skill.get("final_score", 0),
        }
        for skill in paginated
    }

    response = {
        "query": sanitized,
        "page": page,
        "size": size,
        "results": paginated,
        "explain": explain_data,
    }

    cache_set(cache_key, response)
    return response


def get_recommendations(skill_id: str, size: int = 10) -> Dict:
    origin = get_skill_by_id(skill_id)
    if not origin:
        raise ValueError("Skill not found")

    candidates = [s for s in get_all_skills() if s["id"] != skill_id]

    # Exclude near duplicates and same creator spam
    candidates = [s for s in candidates if not near_duplicate(origin, s)]

    # Base relevance by category + tags
    for candidate in candidates:
        score = 0
        if candidate.get("category") == origin.get("category"):
            score += 30
        tag_overlap = len(set(candidate.get("tags", [])) & set(origin.get("tags", [])))
        score += tag_overlap * 10
        score += candidate.get("quality_score", 0) * 0.3
        candidate["recommendation_score"] = score

    candidates.sort(key=lambda x: x["recommendation_score"], reverse=True)

    # Ensure diversity in recommendations
    result = enforce_diversity(candidates, size)

    explain = {
        s["id"]: {
            "relevance": s.get("recommendation_score", 0),
            "quality": s.get("quality_score", 0),
            "creator": s.get("creator_id"),
        }
        for s in result
    }

    return {
        "skill_id": skill_id,
        "recommendations": result,
        "explain": explain,
    }
