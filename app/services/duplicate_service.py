from typing import Dict, List, Optional, Tuple
import hashlib
import json


class DuplicateService:
    def __init__(self, repository):
        """
        repository: DB access layer (skills table)
        Must implement:
            - get_all_skills()
        """
        self.repository = repository

    # ---------------- HASHING ---------------- #

    def calculate_hash(self, data: Dict) -> str:
        structure = {
            "name": (data.get("name") or "").lower(),
            "input_keys": sorted((data.get("input_schema") or {}).keys()),
            "output_keys": sorted((data.get("output_schema") or {}).keys()),
        }

        hash_str = json.dumps(structure, sort_keys=True)
        return hashlib.md5(hash_str.encode()).hexdigest()

    # ---------------- SIMILARITY ---------------- #

    def calculate_similarity(self, skill1: Dict, skill2: Dict) -> float:
        name1 = (skill1.get("name") or "").lower()
        name2 = (skill2.get("name") or "").lower()

        # Name similarity
        if name1 == name2:
            name_score = 1.0
        else:
            words1 = set(name1.split())
            words2 = set(name2.split())
            overlap = len(words1 & words2)
            total = len(words1 | words2)
            name_score = overlap / total if total > 0 else 0

        # Schema similarity
        input1 = set((skill1.get("input_schema") or {}).keys())
        input2 = set((skill2.get("input_schema") or {}).keys())
        output1 = set((skill1.get("output_schema") or {}).keys())
        output2 = set((skill2.get("output_schema") or {}).keys())

        def jaccard(a, b):
            return len(a & b) / len(a | b) if len(a | b) > 0 else 0

        input_score = jaccard(input1, input2)
        output_score = jaccard(output1, output2)

        schema_score = (input_score + output_score) / 2

        # Weighted
        return (0.4 * name_score) + (0.6 * schema_score)

    # ---------------- DETECTION ---------------- #

    def find_duplicates(
        self,
        skill_data: Dict,
        threshold: float = 0.85
    ) -> List[Tuple[str, float]]:
        duplicates = []
        stored_skills = self.repository.get_all_skills()

        for skill in stored_skills:
            similarity = self.calculate_similarity(skill_data, skill)

            if similarity >= threshold:
                duplicates.append((skill["id"], similarity))

        return sorted(duplicates, key=lambda x: x[1], reverse=True)

    def is_exact_duplicate(self, skill_data: Dict) -> Optional[str]:
        skill_hash = self.calculate_hash(skill_data)
        stored_skills = self.repository.get_all_skills()

        for skill in stored_skills:
            if self.calculate_hash(skill) == skill_hash:
                return skill["id"]

        return None

    def is_likely_duplicate(
        self,
        skill_data: Dict,
        threshold: float = 0.9
    ) -> Optional[str]:
        duplicates = self.find_duplicates(skill_data, threshold)

        return duplicates[0][0] if duplicates else None

    def get_near_duplicates(
        self,
        skill_data: Dict,
        threshold: float = 0.75
    ) -> List[Dict]:
        results = []
        duplicates = self.find_duplicates(skill_data, threshold)
        stored_skills = self.repository.get_all_skills()

        skill_map = {s["id"]: s for s in stored_skills}

        for skill_id, similarity in duplicates:
            if skill_id in skill_map:
                results.append({
                    "id": skill_id,
                    "name": skill_map[skill_id].get("name"),
                    "similarity": similarity,
                })

        return results