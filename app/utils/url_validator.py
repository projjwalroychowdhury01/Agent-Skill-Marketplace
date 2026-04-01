"""
URL validation utility - validates URLs and sources.
"""

from typing import Optional, Tuple
import re


def is_valid_url(url: str) -> bool:
    """Check if URL is valid format."""
    if not isinstance(url, str):
        return False

    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
        r'localhost|'  # localhost
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$',
        re.IGNORECASE
    )

    return bool(url_pattern.match(url))


def validate_source_url(source: Optional[str]) -> Tuple[bool, Optional[str]]:
    """Validate source URL if provided."""
    if source is None:
        return True, None

    if not isinstance(source, str):
        return False, "Source must be a string"

    if len(source.strip()) == 0:
        return True, None  # Empty source is OK

    if is_valid_url(source):
        return True, None

    # Check for common source patterns
    if "@" in source:  # Email or github handle
        return True, None

    if "/" in source and len(source) > 3:  # Path-like
        return True, None

    return False, f"Invalid source URL format: {source}"


def validate_author_email(author: Optional[str]) -> Tuple[bool, Optional[str]]:
    """Validate author email if provided."""
    if author is None:
        return True, None

    if not isinstance(author, str):
        return False, "Author must be a string"

    # Simple email validation
    email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

    if email_pattern.match(author.strip()):
        return True, None

    # Also allow username/handle
    if re.match(r'^[a-zA-Z0-9_-]{3,}$', author.strip()):
        return True, None

    return False, f"Invalid author format: {author}"


def extract_domain(url: str) -> Optional[str]:
    """Extract domain from URL."""
    if not is_valid_url(url):
        return None

    # Extract domain
    match = re.search(r'https?://(?:www\.)?([a-zA-Z0-9.-]+)', url)
    if match:
        return match.group(1)

    return None


def is_trusted_source(url: str, trusted_domains: list = None) -> bool:
    """Check if URL is from trusted source."""
    if trusted_domains is None:
        trusted_domains = [
            "github.com",
            "gitlab.com",
            "huggingface.co",
            "pypi.org",
            "npmjs.com",
        ]

    domain = extract_domain(url)
    if not domain:
        return False

    return any(trusted in domain for trusted in trusted_domains)


def sanitize_url(url: str) -> str:
    """Sanitize URL by removing fragments and normalizing."""
    if not is_valid_url(url):
        return url

    # Remove fragment
    url = url.split("#")[0]

    # Remove query strings (optional)
    # url = url.split("?")[0]

    # Ensure trailing slash consistency
    if "?" not in url and not url.endswith("/"):
        if url.count("/") <= 2:  # Only domain, no path
            url += "/"

    return url
