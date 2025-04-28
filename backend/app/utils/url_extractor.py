from typing import List, Set, Optional
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from .url_validator import URLValidator


class URLExtractor:
    """Utility for extracting and processing URLs from HTML content."""

    def __init__(self, base_url: str, allowed_domains: Optional[List[str]] = None):
        """Initialize URL extractor.

        Args:
            base_url: Base URL for resolving relative URLs
            allowed_domains: List of allowed domains
        """
        self.base_url = base_url
        self.validator = URLValidator(allowed_domains)

    def extract_urls(self, html_content: str) -> Set[str]:
        """Extract unique URLs from HTML content.

        Args:
            html_content: HTML content to extract URLs from

        Returns:
            Set of unique normalized URLs
        """
        soup = BeautifulSoup(html_content, "html.parser")
        urls = set()

        for link in soup.find_all("a", href=True):
            url = self._process_url(link["href"])
            if url:
                urls.add(url)

        return urls

    def _process_url(self, url: str) -> Optional[str]:
        """Process and validate a URL.

        Args:
            url: URL to process

        Returns:
            Normalized URL if valid, None otherwise
        """
        try:
            absolute_url = self.validator.resolve_relative_url(url, self.base_url)
            if self.validator.is_valid_and_allowed(absolute_url):
                return self.validator.normalize_url(absolute_url)
        except Exception:
            pass

        return None
