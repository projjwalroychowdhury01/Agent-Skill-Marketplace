"""
Example requests and test cases for FastAPI Skill Validator.
"""

# ============================================================
# EXAMPLE 1: Good Quality Skill (Should be ACCEPTED)
# ============================================================

EXAMPLE_GOOD_SKILL = {
    "name": "JSON Data Extractor",
    "description": "Extracts specified fields from JSON input and generates structured output. Supports nested field selection with dot notation.",
    "category": "data_extraction",
    "tags": ["json", "data extraction", "parsing"],
    "input_schema": {
        "json_data": "string",
        "fields_to_extract": "array",
        "nested": "boolean"
    },
    "output_schema": {
        "extracted_data": "object",
        "extraction_status": "string",
        "fields_found": "array"
    },
    "examples": [
        {
            "input": {
                "json_data": '{"name": "John", "age": 30, "address": {"city": "NYC"}}',
                "fields_to_extract": ["name", "address.city"],
                "nested": True
            },
            "output": {
                "extracted_data": {"name": "John", "city": "NYC"},
                "extraction_status": "success",
                "fields_found": ["name", "address.city"]
            }
        },
        {
            "input": {
                "json_data": '{"title": "Example"}',
                "fields_to_extract": ["title"],
                "nested": False
            },
            "output": {
                "extracted_data": {"title": "Example"},
                "extraction_status": "success",
                "fields_found": ["title"]
            }
        }
    ],
    "tools_used": ["data_transformation", "json_parsing"],
    "source": "https://github.com/example/json-extractor",
    "author": "dev_team"
}


# ============================================================
# EXAMPLE 2: Skill with Issues (Should be REJECTED)
# ============================================================

EXAMPLE_BAD_SKILL_IDENTICAL_SCHEMA = {
    "name": "Pass Through",
    "description": "Passes data through without modification",
    "category": "utility",
    "tags": ["passthrough", "utility", "identity"],
    "input_schema": {
        "data": "string"
    },
    "output_schema": {
        "data": "string"  # ISSUE: Identical to input schema
    },
    "examples": [],
    "tools_used": [],
}


# ============================================================
# EXAMPLE 3: Missing Description Verb (Should be FLAGGED/REJECTED)
# ============================================================

EXAMPLE_BAD_SKILL_NO_VERB = {
    "name": "Data Tool",
    "description": "This tool is really cool and does amazing things",  # No clear action verb
    "category": "data_extraction",
    "tags": ["data", "tool", "processing"],
    "input_schema": {"input": "string"},
    "output_schema": {"output": "string"},
}


# ============================================================
# EXAMPLE 4: Missing Functional Keyword (Should be FLAGGED/REJECTED)
# ============================================================

EXAMPLE_BAD_SKILL_NO_FUNCTIONAL_KEYWORD = {
    "name": "My Tool",  # ISSUE: No functional keyword
    "description": "Validates and transforms data",
    "category": "data_transformation",
    "tags": ["transformation", "data", "processing"],
    "input_schema": {"data": "string"},
    "output_schema": {"result": "string"},
}


# ============================================================
# EXAMPLE 5: Security Issue - Shell Execution (Should be REJECTED)
# ============================================================

EXAMPLE_BAD_SKILL_SECURITY = {
    "name": "Shell Command Executor",
    "description": "Executes shell commands and returns output",  # ISSUE: Security risk
    "category": "utility",
    "tags": ["shell", "execution", "commands"],
    "input_schema": {"command": "string"},
    "output_schema": {"output": "string"},
}


# ============================================================
# EXAMPLE 6: Duplicate Detection (Should be FLAGGED)
# ============================================================

EXAMPLE_SKILL_DUPLICATE = {
    "name": "JSON Data Extractor",  # Same name as EXAMPLE_GOOD_SKILL
    "description": "Extracts fields from JSON data",
    "category": "data_extraction",
    "tags": ["json", "extraction", "parsing"],
    "input_schema": {"json_data": "string", "fields": "array"},
    "output_schema": {"data": "object", "status": "string"},
}


# ============================================================
# EXAMPLE 7: Reserved Keyword (Should be REJECTED)
# ============================================================

EXAMPLE_BAD_SKILL_RESERVED_KEYWORD = {
    "name": "Email Validator",
    "description": "Validates email addresses",
    "category": "validation",
    "tags": ["email", "validation", "checking"],
    "input_schema": {
        "id": "string",  # ISSUE: 'id' is reserved
        "email": "string"
    },
    "output_schema": {
        "is_valid": "boolean"
    },
}


# ============================================================
# EXAMPLE 8: Too Many Tags (Should be FLAGGED/REJECTED)
# ============================================================

EXAMPLE_BAD_SKILL_MANY_TAGS = {
    "name": "Data Processor",
    "description": "Processes and transforms data",
    "category": "data_transformation",
    "tags": ["tag1", "tag2", "tag3", "tag4", "tag5", "tag6", "tag7"],  # ISSUE: 7 tags, max 6
    "input_schema": {"data": "string"},
    "output_schema": {"result": "string"},
}


# ============================================================
# EXAMPLE 9: Too Few Tags (Should be REJECTED)
# ============================================================

EXAMPLE_BAD_SKILL_FEW_TAGS = {
    "name": "Email Validator",
    "description": "Validates email format",
    "category": "validation",
    "tags": ["email"],  # ISSUE: Only 1 tag, min 3
    "input_schema": {"email": "string"},
    "output_schema": {"valid": "boolean"},
}


# ============================================================
# EXAMPLE 10: Missing Required Field (Should be REJECTED)
# ============================================================

EXAMPLE_BAD_SKILL_MISSING_FIELD = {
    "name": "Text Validator",
    "description": "Validates text",
    "category": "validation",
    # ISSUE: Missing 'tags' field
    "input_schema": {"text": "string"},
    "output_schema": {"valid": "boolean"},
}


# ============================================================
# EXAMPLE 11: Complex Valid Skill (Should be ACCEPTED)
# ============================================================

EXAMPLE_COMPLEX_VALID_SKILL = {
    "name": "CSV to JSON Converter",
    "description": "Converts CSV data into structured JSON format. Handles various delimiters and quote styles. Returns formatted output with metadata.",
    "category": "data_transformation",
    "tags": ["csv", "json", "data conversion"],
    "input_schema": {
        "csv_data": "string",
        "delimiter": "string",
        "has_header": "boolean",
        "encoding": "string"
    },
    "output_schema": {
        "json_data": "array",
        "row_count": "number",
        "column_count": "number",
        "conversion_status": "string"
    },
    "examples": [
        {
            "input": {
                "csv_data": "name,age\nJohn,30\nJane,28",
                "delimiter": ",",
                "has_header": True,
                "encoding": "utf-8"
            },
            "output": {
                "json_data": [
                    {"name": "John", "age": "30"},
                    {"name": "Jane", "age": "28"}
                ],
                "row_count": 2,
                "column_count": 2,
                "conversion_status": "success"
            }
        }
    ],
    "tools_used": ["data_transformation", "csv_parsing"],
    "source": "https://github.com/example/csv-converter",
    "author": "conversion_team"
}


# ============================================================
# CURL EXAMPLES
# ============================================================

CURL_EXAMPLE_GOOD = """
curl -X POST http://localhost:8000/validate-skill \\
  -H "Content-Type: application/json" \\
  -d '{
    "name": "JSON Data Extractor",
    "description": "Extracts specified fields from JSON input and generates structured output",
    "category": "data_extraction",
    "tags": ["json", "data extraction", "parsing"],
    "input_schema": {"json_data": "string", "fields": "array"},
    "output_schema": {"extracted_data": "object", "status": "string"},
    "examples": [{
      "input": {"json_data": "{\\"name\\":\\"John\\"}", "fields": ["name"]},
      "output": {"extracted_data": {"name": "John"}, "status": "success"}
    }],
    "tools_used": ["data_transformation"]
  }'
"""

CURL_EXAMPLE_SECURITY_ISSUE = """
curl -X POST http://localhost:8000/validate-skill \\
  -H "Content-Type: application/json" \\
  -d '{
    "name": "Shell Executor",
    "description": "Executes shell commands",
    "category": "utility",
    "tags": ["shell", "execution", "command"],
    "input_schema": {"command": "string"},
    "output_schema": {"result": "string"}
  }'
"""


# ============================================================
# PYTHON TEST EXAMPLES
# ============================================================

PYTHON_TEST_EXAMPLE = """
import requests
import json

BASE_URL = "http://localhost:8000"

# Test 1: Valid skill
skill = {
    "name": "JSON Data Extractor",
    "description": "Extracts specified fields from JSON input and generates structured output",
    "category": "data_extraction",
    "tags": ["json", "data extraction", "parsing"],
    "input_schema": {"json_data": "string"},
    "output_schema": {"extracted": "object"},
}

response = requests.post(f"{BASE_URL}/validate-skill", json=skill)
print(f"Status: {response.status_code}")
print(f"Result: {json.dumps(response.json(), indent=2)}")

# Test 2: Invalid skill (security issue)
bad_skill = {
    "name": "Shell Executor",
    "description": "Executes shell commands freely",
    "category": "utility",
    "tags": ["shell", "execution", "code"],
    "input_schema": {"cmd": "string"},
    "output_schema": {"out": "string"},
}

response = requests.post(f"{BASE_URL}/validate-skill", json=bad_skill)
print(f"\\nBad Skill Status: {response.status_code}")
print(f"Result: {json.dumps(response.json(), indent=2)}")
"""


# ============================================================
# POSTMAN COLLECTION (JSON FORMAT)
# ============================================================

POSTMAN_COLLECTION = {
    "info": {
        "name": "Skill Validator API",
        "description": "Test collection for FastAPI Skill Validator",
        "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
    },
    "item": [
        {
            "name": "Validate Good Skill",
            "request": {
                "method": "POST",
                "header": [
                    {"key": "Content-Type", "value": "application/json"}
                ],
                "url": {"raw": "{{base_url}}/validate-skill", "host": ["{{base_url}}"], "path": ["validate-skill"]},
                "body": {
                    "mode": "raw",
                    "raw": json.dumps(EXAMPLE_GOOD_SKILL, indent=2)
                }
            }
        },
        {
            "name": "Validate Bad Skill (Security)",
            "request": {
                "method": "POST",
                "header": [
                    {"key": "Content-Type", "value": "application/json"}
                ],
                "url": {"raw": "{{base_url}}/validate-skill", "host": ["{{base_url}}"], "path": ["validate-skill"]},
                "body": {
                    "mode": "raw",
                    "raw": json.dumps(EXAMPLE_BAD_SKILL_SECURITY, indent=2)
                }
            }
        },
        {
            "name": "Health Check",
            "request": {
                "method": "GET",
                "url": {"raw": "{{base_url}}/health", "host": ["{{base_url}}"], "path": ["health"]}
            }
        }
    ],
    "variable": [
        {"key": "base_url", "value": "http://localhost:8000"}
    ]
}


if __name__ == "__main__":
    print("Example Skills and Test Cases")
    print("=" * 80)
    print()
    print("Good Skill Example:")
    print(json.dumps(EXAMPLE_GOOD_SKILL, indent=2))
    print()
    print("Bad Skill Examples:")
    print()
    print("1. Identical Schemas:")
    print(json.dumps(EXAMPLE_BAD_SKILL_IDENTICAL_SCHEMA, indent=2))
    print()
    print("2. Security Issue:")
    print(json.dumps(EXAMPLE_BAD_SKILL_SECURITY, indent=2))
