from models import IntelligenceEngineRequest, FeedbackSignals
from utils.intelligence_engine import run_intelligence_engine

req = IntelligenceEngineRequest(
    validated_skill={
        "name": "python tool",
        "category": "automation",
        "description": "this is a basic test " * 5,
        "quality_score": 85,
        "input_schema": {"test": "str"},
        "output_schema": {}
    },
    existing_skills=[
        {
            "id": "skill-123",
            "name": "python script",
            "category": "automation",
            "input_schema": {"test": "str"},
            "output_schema": {}
        }
    ],
    feedback_signals=FeedbackSignals(click_rate=0.5, usage_count=10, user_rating=4.5)
)

print(run_intelligence_engine(req).dict())
