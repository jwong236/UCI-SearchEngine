from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, field


@dataclass
class CrawlStatistics:
    """Statistics for a crawl operation."""

    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    total_urls: int = 0
    processed_urls: int = 0
    failed_urls: int = 0
    skipped_urls: int = 0
    rate_limited_urls: int = 0
    domain_stats: Dict[str, Dict[str, int]] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)

    def update(self, url: str, status: str, error: Optional[str] = None) -> None:
        """Update statistics.

        Args:
            url: URL that was processed
            status: Status of processing
            error: Error message if any
        """
        self.total_urls += 1

        if status == "processed":
            self.processed_urls += 1
        elif status == "failed":
            self.failed_urls += 1
        elif status == "skipped":
            self.skipped_urls += 1
        elif status == "rate_limited":
            self.rate_limited_urls += 1

        if error:
            self.errors.append(f"{url}: {error}")

        domain = url.split("/")[2]
        if domain not in self.domain_stats:
            self.domain_stats[domain] = {
                "total": 0,
                "processed": 0,
                "failed": 0,
                "skipped": 0,
                "rate_limited": 0,
            }

        self.domain_stats[domain]["total"] += 1
        self.domain_stats[domain][status] += 1

    def complete(self) -> None:
        """Mark statistics as complete."""
        self.end_time = datetime.now()

    def get_summary(self) -> Dict[str, any]:
        """Get summary of statistics.

        Returns:
            Dictionary with statistics summary
        """
        duration = (self.end_time or datetime.now()) - self.start_time

        return {
            "duration_seconds": duration.total_seconds(),
            "total_urls": self.total_urls,
            "processed_urls": self.processed_urls,
            "failed_urls": self.failed_urls,
            "skipped_urls": self.skipped_urls,
            "rate_limited_urls": self.rate_limited_urls,
            "success_rate": (
                (self.processed_urls / self.total_urls * 100)
                if self.total_urls > 0
                else 0
            ),
            "domain_stats": self.domain_stats,
            "error_count": len(self.errors),
        }
