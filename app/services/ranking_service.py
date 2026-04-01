from typing import Dict, List
from math import log
from datetime import datetime

from app.db.repository import SkillRepository


class RankingService:
    def __init__(self, repository: SkillRepository):
        self.repository = repository

    # ---------------- QUERY PROCESSING ---------------- #

    def preprocess_query(self, query: str) -> List[str]:
        return [t.lower() for t in query.split() if t.strip()]

    # ---------------- SCORING ---------------- #

    def calculate_relevance(self, skill: Dict, tokens: List[str]) -> float:
        text = f"{skill.get('name')} {skill.get('description')} {' '.join(skill.get('tags', []))}".lower()

        hits = sum(1 for token in tokens if token in text)
        return 100.0 * hits / (len(tokens) if tokens else 1)

    def calculate_popularity(self, skill: Dict) -> float:
        usage = float(skill.get("usage_count", 0))
        saves = float(skill.get("save_count", 0))
        rating = float(skill.get("rating_avg", 0))

        return log(1 + usage + saves + rating)

    def calculate_freshness(self, skill: Dict) -> float:
        created = skill.get("created_at")
        if not created:
            return 0.0

        age = (datetime.utcnow() - created).days
        return max(0.0, 100 - age)

    # ---------------- NORMALIZATION ---------------- #

    def normalize(self, values: List[float]) -> List[float]:
        if not values:
            return []

        vmin, vmax = min(values), max(values)
        if vmin == vmax:
            return [100.0] * len(values)

        return [(v - vmin) / (vmax - vmin) * 100 for v in values]

    # ---------------- MAIN RANKING ---------------- #

    def rank(self, query: str, page: int = 1, size: int = 10) -> Dict:
        tokens = self.preprocess_query(query)

        skills = self.repository.get_all_skills()

        if not skills:
            return {"results": [], "total": 0}

        # Compute raw scores
        for skill in skills:
            skill["relevance"] = self.calculate_relevance(skill, tokens)
            skill["quality"] = skill.get("quality_score", 0)
            skill["popularity"] = self.calculate_popularity(skill)
            skill["freshness"] = self.calculate_freshness(skill)

        # Normalize
        rel = self.normalize([s["relevance"] for s in skills])
        qual = self.normalize([s["quality"] for s in skills])
        pop = self.normalize([s["popularity"] for s in skills])
        fresh = self.normalize([s["freshness"] for s in skills])

        # Final score (aligned with your strategy)
        for i, skill in enumerate(skills):
            skill["final_score"] = (
                0.5 * rel[i] +
                0.3 * qual[i] +
                0.1 * pop[i] +
                0.1 * fresh[i]
            )

        ranked = sorted(skills, key=lambda x: x["final_score"], reverse=True)

        # Pagination
        start = (page - 1) * size
        end = start + size

        return {
            "results": ranked[start:end],
            "total": len(ranked)
        }