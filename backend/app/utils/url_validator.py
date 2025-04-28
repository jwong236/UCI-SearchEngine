from typing import List, Optional
from urllib.parse import urlparse, urljoin
import re


class URLValidator:
    """Utility for validating and normalizing URLs."""

    def __init__(self, allowed_domains: Optional[List[str]] = None):
        """Initialize URL validator.

        Args:
            allowed_domains: List of allowed domains
        """
        self.allowed_domains = allowed_domains or []
        self._compiled_domains = [re.compile(domain) for domain in self.allowed_domains]
        self.url_pattern = re.compile(
            r"^https?://"  # http:// or https://
            r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"  # domain
            r"localhost|"  # localhost
            r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # IP
            r"(?::\d+)?"  # optional port
            r"(?:/?|[/?]\S+)$",
            re.IGNORECASE,
        )

    def normalize_url(self, url: str) -> str:
        """Normalize URL by removing fragments and trailing slashes.

        Args:
            url: URL to normalize

        Returns:
            str: Normalized URL
        """
        parsed = urlparse(url)
        path = parsed.path.rstrip("/")
        return f"{parsed.scheme}://{parsed.netloc}{path}"

    def is_valid_url(self, url: str) -> bool:
        """Check if URL is valid.

        Args:
            url: URL to validate

        Returns:
            bool: True if URL is valid
        """
        try:
            return bool(self.url_pattern.match(url))
        except Exception:
            return False

    def is_allowed_domain(self, url: str) -> bool:
        """Check if URL's domain is allowed.

        Args:
            url: URL to check

        Returns:
            bool: True if domain is allowed
        """
        if not self.allowed_domains:
            return True

        try:
            domain = urlparse(url).netloc.lower()
            return any(domain.endswith(d.lower()) for d in self.allowed_domains)
        except Exception:
            return False

    def is_valid_and_allowed(self, url: str) -> bool:
        """Check if URL is valid and allowed.

        Args:
            url: URL to check

        Returns:
            bool: True if URL is valid and allowed
        """
        try:
            parsed = urlparse(url)
            if not all([parsed.scheme, parsed.netloc]):
                return False

            if self.allowed_domains:
                return any(
                    pattern.match(parsed.netloc) for pattern in self._compiled_domains
                )

            return True
        except Exception:
            return False

    def get_domain(self, url: str) -> Optional[str]:
        """Extract domain from URL.

        Args:
            url: URL to process

        Returns:
            Optional[str]: Domain name or None if invalid
        """
        try:
            return urlparse(url).netloc
        except:
            return None

    def is_same_domain(self, url1: str, url2: str) -> bool:
        """Check if two URLs are from the same domain.

        Args:
            url1: First URL
            url2: Second URL

        Returns:
            bool: True if URLs are from same domain
        """
        try:
            domain1 = urlparse(url1).netloc
            domain2 = urlparse(url2).netloc
            return domain1 == domain2
        except Exception:
            return False

    def resolve_relative_url(self, url: str, base_url: str) -> str:
        """Resolve relative URL against base URL.

        Args:
            url: URL to resolve
            base_url: Base URL to resolve against

        Returns:
            Absolute URL
        """
        return urljoin(base_url, url)
