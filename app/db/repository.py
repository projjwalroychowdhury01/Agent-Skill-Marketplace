from typing import List, Dict


class SkillRepository:
    def __init__(self, db_session=None):
        self.db = db_session  # later: SQLAlchemy session

    def get_all_skills(self) -> List[Dict]:
        """
        TEMP: Replace later with real DB query
        """
        return []

    def get_skill_by_id(self, skill_id: str) -> Dict:
        """
        Fetch single skill
        """
        return {}

    def save_skill(self, skill_data: Dict) -> None:
        """
        Store skill in DB
        """
        pass