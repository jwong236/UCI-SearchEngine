from typing import Set, Optional
from urllib.parse import urljoin, urlparse
from .url_validator import URLValidator


class URLProcessor:
    """Utility for processing and managing URLs."""

    def __init__(self, base_url: str, allowed_domains: Optional[list[str]] = None):
        """Initialize URL processor.

        Args:
            base_url: Base URL for the crawler
            allowed_domains: List of allowed domains
        """
        self.base_url = base_url
        self.validator = URLValidator(allowed_domains)
        self.processed_urls: Set[str] = set()
        self.failed_urls: Set[str] = set()

    def should_process_url(self, url: str) -> bool:
        """Check if URL should be processed.

        Args:
            url: URL to check

        Returns:
            True if URL should be processed
        """
        normalized_url = self.validator.normalize_url(url)
        if normalized_url in self.processed_urls:
            return False

        if not self.validator.is_valid_and_allowed(url):
            return False

        return True

    def mark_url_processed(self, url: str) -> None:
        """Mark URL as processed.

        Args:
            url: URL to mark as processed
        """
        self.processed_urls.add(self.validator.normalize_url(url))

    def add_failed(self, url: str) -> None:
        """Mark URL as failed.

        Args:
            url: URL to mark as failed
        """
        self.failed_urls.add(self.validator.normalize_url(url))

    def is_processed(self, url: str) -> bool:
        """Check if URL has been processed.

        Args:
            url: URL to check

        Returns:
            bool: True if URL has been processed
        """
        return self.validator.normalize_url(url) in self.processed_urls

    def is_failed(self, url: str) -> bool:
        """Check if URL has failed.

        Args:
            url: URL to check

        Returns:
            bool: True if URL has failed
        """
        return self.validator.normalize_url(url) in self.failed_urls

    def get_new_links(self, base_url: str, links: list[str]) -> list[str]:
        """Get new unprocessed links from page.

        Args:
            base_url: Base URL of the page
            links: List of links found on page

        Returns:
            list[str]: List of new valid links
        """
        new_links = []
        for link in links:
            try:
                absolute_url = urljoin(base_url, link)
                normalized_url = self.validator.normalize_url(absolute_url)

                if (
                    self.validator.is_valid_url(normalized_url)
                    and self.validator.is_allowed_domain(normalized_url)
                    and not self.is_processed(normalized_url)
                    and not self.is_failed(normalized_url)
                ):
                    new_links.append(normalized_url)
            except Exception:
                continue

        return new_links

    def reset(self) -> None:
        """Reset processor state."""
        self.processed_urls.clear()
        self.failed_urls.clear()

    def get_stats(self) -> dict:
        """Get processing statistics.

        Returns:
            dict: Statistics about processed and failed URLs
        """
        return {
            "processed": len(self.processed_urls),
            "failed": len(self.failed_urls),
            "total": len(self.processed_urls) + len(self.failed_urls),
        }

    def get_domain(self, url: str) -> Optional[str]:
        """Get domain from URL.

        Args:
            url: URL to get domain from

        Returns:
            Domain if valid, None otherwise
        """
        try:
            return urlparse(url).netloc
        except Exception:
            return None

    def is_same_domain(self, url1: str, url2: str) -> bool:
        """Check if two URLs are from the same domain.

        Args:
            url1: First URL
            url2: Second URL

        Returns:
            True if URLs are from same domain
        """
        domain1 = self.get_domain(url1)
        domain2 = self.get_domain(url2)
        return domain1 and domain2 and domain1 == domain2
