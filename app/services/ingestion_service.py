from typing import Dict, Any, List
import requests

from app.services.validation_service import ValidationService
from app.services.normalization_service import normalize_with_llm  # we will create next
from app.db.repository import SkillRepository


class IngestionService:
    def __init__(self):
        self.validation_service = ValidationService()
        self.repository = SkillRepository()

    # ---------------- GITHUB FETCH ---------------- #

    def fetch_repo_data(self, repo_url: str) -> Dict[str, Any]:
        """
        Extract basic repo data using GitHub API
        """
        try:
            if "github.com" not in repo_url:
                return None, None

            parts = repo_url.strip("/").split("/")
            if len(parts) < 2:
                return None, None
            owner, repo = parts[-2], parts[-1]

            api_url = f"https://api.github.com/repos/{owner}/{repo}"
            response = requests.get(api_url)

            if response.status_code != 200:
                return {}

            data = response.json()

            return {
                "name": data.get("name"),
                "description": data.get("description"),
                "stars": data.get("stargazers_count"),
                "updated_at": data.get("updated_at"),
                "default_branch": data.get("default_branch"),
                "owner": owner,
                "repo": repo,
            }

        except Exception:
            return {}

    def fetch_readme(self, owner: str, repo: str) -> str:
        url = f"https://api.github.com/repos/{owner}/{repo}/readme"

        try:
            res = requests.get(url, headers = {
                    "Accept": "application/vnd.github.v3+json",
                    # optional:
                    # "Authorization": f"Bearer {GITHUB_TOKEN}"
                })
            if res.status_code == 200:
                return res.text[:5000]
            if res.status_code == 403:
                return {"error": "rate_limited"}
        except Exception:
            pass

        return ""

    # ---------------- SANITIZATION ---------------- #

    def sanitize_text(self, text: str) -> str:
        """
        Remove unsafe patterns before LLM
        """
        if not text:
            return ""

        blacklist = [
            "ignore previous instructions",
            "execute this",
            "run this code",
            "system prompt",
        ]

        text_lower = text.lower()
        for bad in blacklist:
            if bad in text_lower:
                return ""

        return text[:5000]

    # ---------------- INGEST ---------------- #

    def ingest_repo(self, repo_url: str) -> Dict[str, Any]:
        """
        Full ingestion pipeline
        """

        # Step 1: Fetch repo metadata
        repo_data = self.fetch_repo_data(repo_url)

        if not repo_data:
            return {"status": "FAILED", "reason": "Invalid repo"}

        # Step 2: Pre-filter (CRITICAL)
        if repo_data.get("stars", 0) < 20:
            return {"status": "REJECTED", "reason": "Low quality repo"}

        # Step 3: Fetch README
        readme = self.fetch_readme(repo_data["owner"], repo_data["repo"])

        if not readme:
            return {"status": "REJECTED", "reason": "No README"}

        # Step 4: Sanitize
        clean_readme = self.sanitize_text(readme)

        # Step 5: Normalize using LLM
        structured_skill = normalize_with_llm({
            "readme": clean_readme,
            "repo": repo_data
        })

        if not structured_skill:
            return {"status": "FAILED", "reason": "LLM normalization failed"}

        # Step 6: Validate
        validation_result = self.validation_service.validate(structured_skill)

        if validation_result.status != "ACCEPTED":
            return {
                "status": validation_result.status,
                "errors": validation_result.errors,
                "warnings": validation_result.warnings,
            }

        # Step 7: Store
        self.repository.save_skill(validation_result.normalized_skill)

        return {
            "status": "SUCCESS",
            "quality_score": validation_result.quality_score
        }