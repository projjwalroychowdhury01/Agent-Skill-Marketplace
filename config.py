"""
Configuration for FastAPI Skill Validator.
"""

import os
from typing import List, Set

# Environment
ENV = os.getenv("ENV", "development")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Validator Settings
VALIDATION_SETTINGS = {
    # Structural constraints
    "name_min_length": 3,
    "name_max_length": 60,
    "description_max_length": 300,
    "description_min_length": 20,
    "tags_min_count": 3,
    "tags_max_count": 6,
    
    # Similarity thresholds
    "exact_duplicate_threshold": 1.0,
    "likely_duplicate_threshold": 0.9,
    "near_duplicate_threshold": 0.75,
    
    # Security
    "security_strict_mode": os.getenv("SECURITY_STRICT_MODE", "true").lower() == "true",
    "allow_shell_operations": False,
    "allow_arbitrary_code_execution": False,
    
    # Quality scoring
    "min_acceptable_score": 50,
    "good_quality_score": 75,
    
    # Flags
    "flag_on_near_duplicates": True,
    "flag_on_warnings": True,
    "auto_reject_security_issues": True,
}

# Valid categories
VALID_CATEGORIES: Set[str] = {
    "data_extraction",
    "data_transformation",
    "text_processing",
    "image_processing",
    "api_integration",
    "database_operations",
    "authentication",
    "content_generation",
    "classification",
    "prediction",
    "analysis",
    "utility",
}

# Reserved keywords (cannot use in schemas)
RESERVED_KEYWORDS: Set[str] = {
    "id",
    "created_at",
    "updated_at",
    "system",
}

# Security - dangerous patterns
DANGEROUS_PATTERNS: List[str] = [
    "execute shell",
    "run arbitrary code",
    "bypass security",
    "eval(",
    "exec(",
    "__import__",
    "subprocess",
    "os.system",
    "system(",
    "shell=true",
]

# Security - suspicious keywords
SUSPICIOUS_KEYWORDS: List[str] = [
    "delete all",
    "drop table",
    "truncate",
    "destroy database",
    "remove all users",
    "unauthorized access",
    "steal data",
    "crack password",
]

# Functional keywords (for name quality)
FUNCTIONAL_KEYWORDS: List[str] = [
    "extractor",
    "converter",
    "validator",
    "generator",
    "parser",
    "classifier",
    "transformer",
    "aggregator",
    "filter",
    "mapper",
    "encoder",
    "decoder",
    "analyzer",
    "builder",
    "processor",
]

# Controlled tag vocabulary
CONTROLLED_TAGS: Set[str] = {
    "data extraction",
    "data transformation",
    "data validation",
    "text processing",
    "image processing",
    "api integration",
    "database operations",
    "authentication",
    "content generation",
    "classification",
    "prediction",
    "analysis",
    "aggregation",
    "filtering",
    "sorting",
    "mapping",
    "encoding",
    "decoding",
    "parsing",
    "formatting",
}

# Ranking and recommendation settings
RANKING_WEIGHTS = {
    "relevance": 0.30,
    "quality": 0.25,
    "popularity": 0.15,
    "freshness": 0.15,
    "completeness": 0.10,
    "exploration": 0.05,
}

RANKING_THRESHOLDS = {
    "min_relevance": 40,
    "min_quality": 60,
    "max_query_length": 200,
}

EXPLORATION_SETTINGS = {
    "cold_start_threshold": 50,
    "boost_factor": 20,
    "decay_days": 30,
}

ANTI_SPAM_SETTINGS = {
    "max_repeated_token_ratio": 0.75,
    "keyword_stuffing_penalty": 0.5,
}

DIVERSITY_SETTINGS = {
    "max_per_creator": 2,
    "required_category_frac": 0.3,
}

CACHE_SETTINGS = {
    "query_cache_size": 500,
    "result_ttl_seconds": 120,
}

# Logging configuration
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s"
        },
    },
    "handlers": {
        "default": {
            "level": LOG_LEVEL,
            "class": "logging.StreamHandler",
            "formatter": "standard",
        },
    },
    "loggers": {
        "": {
            "handlers": ["default"],
            "level": LOG_LEVEL,
            "propagate": True,
        }
    },
}
