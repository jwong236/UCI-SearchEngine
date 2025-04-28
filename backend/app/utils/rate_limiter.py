from typing import Dict, Optional
from datetime import datetime, timedelta
import time


class RateLimiter:
    """Utility for managing request rate limits."""

    def __init__(self, requests_per_second: float = 1.0):
        """Initialize rate limiter.

        Args:
            requests_per_second: Maximum requests per second
        """
        self.min_interval = 1.0 / requests_per_second
        self.last_request_time: Dict[str, float] = {}

    def should_process(self, domain: str) -> bool:
        """Check if request should be processed.

        Args:
            domain: Domain to check

        Returns:
            True if request should be processed
        """
        current_time = time.time()
        last_time = self.last_request_time.get(domain, 0)

        if current_time - last_time < self.min_interval:
            return False

        self.last_request_time[domain] = current_time
        return True

    def wait_if_needed(self, domain: str) -> None:
        """Wait if rate limit would be exceeded.

        Args:
            domain: Domain to check
        """
        current_time = time.time()
        last_time = self.last_request_time.get(domain, 0)

        if current_time - last_time < self.min_interval:
            time.sleep(self.min_interval - (current_time - last_time))

        self.last_request_time[domain] = time.time()

    def get_next_allowed_time(self, domain: str) -> Optional[datetime]:
        """Get next allowed request time.

        Args:
            domain: Domain to check

        Returns:
            Next allowed time if rate limited, None otherwise
        """
        current_time = time.time()
        last_time = self.last_request_time.get(domain, 0)

        if current_time - last_time < self.min_interval:
            return datetime.fromtimestamp(last_time + self.min_interval)

        return None

    def get_wait_time(self, domain: str) -> float:
        """Get time to wait before next request.

        Args:
            domain: Domain to check wait time for

        Returns:
            float: Seconds to wait
        """
        now = datetime.now()
        last_time = self.last_request_time.get(domain)

        if not last_time:
            return 0.0

        time_since_last = (now - last_time).total_seconds()
        wait_time = max(0.0, self.min_interval - time_since_last)
        return wait_time

    def reset(self, domain: Optional[str] = None):
        """Reset rate limiter state.

        Args:
            domain: Domain to reset, or None for all domains
        """
        if domain:
            self.last_request_time.pop(domain, None)
        else:
            self.last_request_time.clear()

    def get_last_request_time(self, domain: str) -> datetime:
        """Get time of last request for domain.

        Args:
            domain: Domain to check

        Returns:
            datetime: Timestamp of last request
        """
        return self.last_request_time.get(domain)
