"""
Test suite for FastAPI Skill Validator.
Run with: pytest test_validator.py -v
"""

import pytest
from fastapi.testclient import TestClient
from main import app
from utils.duplicate_detector import add_skill_to_database, clear_database


client = TestClient(app)


@pytest.fixture(autouse=True)
def cleanup():
    """Clear test database before each test."""
    clear_database()
    yield
    clear_database()


class TestHealthCheck:
    """Health check and root endpoints."""

    def test_health_endpoint(self):
        """Test health check."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_root_endpoint(self):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        assert response.json()["name"] == "Agent Skill Validator"


class TestValidValidSkills:
    """Test valid skills that should be ACCEPTED."""

    def test_simple_valid_skill(self):
        """Test basic valid skill."""
        skill = {
            "name": "JSON Data Extractor",
            "description": "Extracts specified fields from JSON objects and returns structured output",
            "category": "data_extraction",
            "tags": ["json", "data extraction", "parsing"],
            "input_schema": {"json_data": "string", "fields": "array"},
            "output_schema": {"extracted_data": "object", "status": "string"},
            "examples": [
                {
                    "input": {"json_data": '{"name":"John"}', "fields": ["name"]},
                    "output": {"extracted_data": {"name": "John"}, "status": "success"},
                }
            ],
            "tools_used": ["data_transformation"],
        }

        response = client.post("/validate-skill", json=skill)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["ACCEPTED", "FLAGGED"]
        assert data["quality_score"] > 0

    def test_minimal_valid_skill(self):
        """Test minimal valid skill."""
        skill = {
            "name": "Text Validator",
            "description": "Validates text input and returns validation result",
            "category": "validation",
            "tags": ["text", "validation", "checking"],
            "input_schema": {"text": "string"},
            "output_schema": {"is_valid": "boolean"},
        }

        response = client.post("/validate-skill", json=skill)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["ACCEPTED", "FLAGGED"]


class TestStructuralValidation:
    """Test structural validation failures."""

    def test_missing_required_field(self):
        """Test rejection when required field is missing."""
        skill = {
            "name": "Test Skill",
            "description": "Test",
            "category": "data_extraction",
            # Missing tags
            "input_schema": {"a": "string"},
            "output_schema": {"b": "string"},
        }

        response = client.post("/validate-skill", json=skill)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "REJECTED"
        assert len(data["errors"]) > 0

    def test_wrong_field_type(self):
        """Test rejection when field has wrong type."""
        skill = {
            "name": "Test Skill",
            "description": "Test description",
            "category": "data_extraction",
            "tags": "not_a_list",  # Should be list
            "input_schema": {"a": "string"},
            "output_schema": {"b": "string"},
        }

        response = client.post("/validate-skill", json=skill)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "REJECTED"

    def test_field_constraint_name_too_long(self):
        """Test rejection when name exceeds max length."""
        skill = {
            "name": "A" * 100,  # Exceeds 60 char limit
            "description": "Test description",
            "category": "data_extraction",
            "tags": ["tag1", "tag2", "tag3"],
            "input_schema": {"a": "string"},
            "output_schema": {"b": "string"},
        }

        response = client.post("/validate-skill", json=skill)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "REJECTED"

    def test_too_many_tags(self):
        """Test rejection when too many tags."""
        skill = {
            "name": "Test Skill",
            "description": "Test description",
            "category": "data_extraction",
            "tags": ["a", "b", "c", "d", "e", "f", "g"],  # 7 tags, max is 6
            "input_schema": {"a": "string"},
            "output_schema": {"b": "string"},
        }

        response = client.post("/validate-skill", json=skill)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["REJECTED", "FLAGGED"]  # Should flag or reject

    def test_reserved_keyword_in_schema(self):
        """Test rejection when reserved keyword used in schema."""
        skill = {
            "name": "Test Skill",
            "description": "Test description",
            "category": "data_extraction",
            "tags": ["tag1", "tag2", "tag3"],
            "input_schema": {"id": "string"},  # Reserved word
            "output_schema": {"b": "string"},
        }

        response = client.post("/validate-skill", json=skill)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "REJECTED"


class TestSemanticValidation:
    """Test semantic validation."""

    def test_identical_input_output_schemas(self):
        """Test rejection when input == output schema."""
        skill = {
            "name": "Test Skill",
            "description": "Test description that does nothing",
            "category": "data_extraction",
            "tags": ["tag1", "tag2", "tag3"],
            "input_schema": {"field": "string"},
            "output_schema": {"field": "string"},  # Same as input
        }

        response = client.post("/validate-skill", json=skill)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "REJECTED"

    def test_missing_description_verb(self):
        """Test rejection when description lacks action verb."""
        skill = {
            "name": "Test Skill",
            "description": "This is a tool that does something",  # No clear verb
            "category": "data_extraction",
            "tags": ["tag1", "tag2", "tag3"],
            "input_schema": {"a": "string"},
            "output_schema": {"b": "string"},
        }

        response = client.post("/validate-skill", json=skill)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["REJECTED", "FLAGGED"]

    def test_missing_functional_keyword_in_name(self):
        """Test rejection when name lacks functional keyword."""
        skill = {
            "name": "My Tool",  # No functional keyword
            "description": "Validates and transforms data",
            "category": "data_extraction",
            "tags": ["tag1", "tag2", "tag3"],
            "input_schema": {"a": "string"},
            "output_schema": {"b": "string"},
        }

        response = client.post("/validate-skill", json=skill)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["REJECTED", "FLAGGED"]


class TestSecurityValidation:
    """Test security validation."""

    def test_dangerous_pattern_shell_execution(self):
        """Test rejection of shell execution patterns."""
        skill = {
            "name": "Shell Command Validator",
            "description": "Validates and executes shell commands",
            "category": "utility",
            "tags": ["shell", "command", "execution"],
            "input_schema": {"command": "string"},
            "output_schema": {"output": "string"},
        }

        response = client.post("/validate-skill", json=skill)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "REJECTED"
        # Should have security error

    def test_malicious_intent_delete(self):
        """Test rejection of malicious intent."""
        skill = {
            "name": "Database Cleaner",
            "description": "Deletes all database records",
            "category": "database_operations",
            "tags": ["database", "delete", "cleanup"],
            "input_schema": {"table": "string"},
            "output_schema": {"deleted": "number"},
        }

        response = client.post("/validate-skill", json=skill)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "REJECTED"


class TestQualityScoring:
    """Test quality scoring."""

    def test_good_quality_skill(self):
        """Test good quality skill gets high score."""
        skill = {
            "name": "JSON Data Extractor",
            "description": "Extracts specified fields from JSON input and generates structured output with metadata",
            "category": "data_extraction",
            "tags": ["json", "data extraction", "parsing"],
            "input_schema": {"json_data": "string", "fields_to_extract": "array"},
            "output_schema": {"extracted_data": "object", "extraction_status": "string"},
            "examples": [
                {
                    "input": {"json_data": '{"name":"John"}', "fields_to_extract": ["name"]},
                    "output": {"extracted_data": {"name": "John"}, "extraction_status": "success"},
                },
                {
                    "input": {"json_data": '{"age":30}', "fields_to_extract": ["age"]},
                    "output": {"extracted_data": {"age": 30}, "extraction_status": "success"},
                },
            ],
            "tools_used": ["data_transformation"],
        }

        response = client.post("/validate-skill", json=skill)
        assert response.status_code == 200
        data = response.json()
        assert data["quality_score"] >= 60

    def test_score_breakdown_exists(self):
        """Test that score breakdown is provided."""
        skill = {
            "name": "JSON Parser",
            "description": "Parses JSON strings into objects",
            "category": "data_extraction",
            "tags": ["json", "parser", "parsing"],
            "input_schema": {"json_string": "string"},
            "output_schema": {"parsed_object": "object"},
        }

        response = client.post("/validate-skill", json=skill)
        assert response.status_code == 200
        data = response.json()
        breakdown = data["score_breakdown"]
        assert "description_quality" in breakdown
        assert "example_quality" in breakdown
        assert "tag_quality" in breakdown
        assert breakdown["total"] > 0


class TestNormalization:
    """Test normalization."""

    def test_tags_normalized(self):
        """Test that tags are normalized."""
        skill = {
            "name": "Data Transformer",
            "description": "Transforms data structures",
            "category": "data_transformation",
            "tags": ["  DATA TRANSFORMATION  ", "etl", "mapping"],
            "input_schema": {"a": "string"},
            "output_schema": {"b": "string"},
        }

        response = client.post("/validate-skill", json=skill)
        assert response.status_code == 200
        data = response.json()
        if data["normalized_skill"]:
            # Tags should be lowercase and trimmed
            tags = data["normalized_skill"]["tags"]
            assert all(tag == tag.lower() for tag in tags)


class TestDuplicateDetection:
    """Test duplicate detection."""

    def test_exact_duplicate_detected(self):
        """Test exact duplicate is detected."""
        skill = {
            "name": "JSON Extractor",
            "description": "Extracts JSON fields",
            "category": "data_extraction",
            "tags": ["json", "extract", "parsing"],
            "input_schema": {"data": "string"},
            "output_schema": {"result": "object"},
        }

        # Add to database
        add_skill_to_database("skill-001", skill)

        # Submit duplicate
        response = client.post("/validate-skill", json=skill)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "REJECTED"
        assert data["duplicate_detected"] is True


class TestSearchAndRecommendations:
    """Test ranking and recommendation endpoints."""

    def test_search_skills(self):
        response = client.get("/skills/search", params={"query": "json extraction", "page": 1, "size": 5})
        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "json extraction"
        assert "results" in data
        assert isinstance(data["results"], list)

    def test_search_spam_detection(self):
        response = client.get("/skills/search", params={"query": "foo foo foo foo foo foo", "page": 1, "size": 5})
        assert response.status_code == 400

    def test_skill_recommendations(self):
        # use a known preloaded skill id from skill_catalog
        known_id = "skill-001"
        response = client.get(f"/skills/{known_id}/recommendations", params={"size": 3})
        assert response.status_code == 200
        data = response.json()
        assert data["skill_id"] == known_id
        assert "recommendations" in data
        assert isinstance(data["recommendations"], list)


class TestErrorHandling:
    """Test error handling."""

    def test_invalid_json(self):
        """Test invalid JSON handling."""
        response = client.post("/validate-skill", data="invalid json")
        assert response.status_code == 422

    def test_empty_body(self):
        """Test empty body handling."""
        response = client.post("/validate-skill", json={})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "REJECTED"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
