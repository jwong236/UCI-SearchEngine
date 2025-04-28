from urllib.parse import urlparse, urljoin
from typing import Optional
import re


class URLValidator:
    """URL validation and manipulation utility."""

    UCI_DOMAINS = {
        "uci.edu",
        "www.uci.edu",
        "ics.uci.edu",
        "www.ics.uci.edu",
        "cs.uci.edu",
        "www.cs.uci.edu",
        "informatics.uci.edu",
        "www.informatics.uci.edu",
        "stat.uci.edu",
        "www.stat.uci.edu",
    }

    @classmethod
    def is_valid_uci_url(cls, url: str) -> bool:
        """Check if URL is a valid UCI URL."""
        try:
            parsed = urlparse(url)
            return (
                parsed.scheme in {"http", "https"}
                and parsed.netloc.lower() in cls.UCI_DOMAINS
                and not cls._is_file_extension(parsed.path)
            )
        except Exception:
            return False

    @classmethod
    def normalize_url(cls, url: str, base_url: Optional[str] = None) -> str:
        """Normalize URL by removing fragments and joining with base if provided."""
        if base_url:
            url = urljoin(base_url, url)
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

    @classmethod
    def _is_file_extension(cls, path: str) -> bool:
        """Check if path has a file extension."""
        return bool(re.search(r"\.[a-zA-Z0-9]{2,4}$", path))
