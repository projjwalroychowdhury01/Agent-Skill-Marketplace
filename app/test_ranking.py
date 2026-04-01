from app.db.repository import SkillRepository
from app.services.ranking_service import RankingService


def test_ranking():
    repo = SkillRepository()
    ranking_service = RankingService(repo)

    results = ranking_service.rank(
        query="ai agent",
        page=1,
        size=10
    )

    print(results)


if __name__ == "__main__":
    test_ranking()