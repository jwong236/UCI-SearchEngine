from dataclasses import dataclass
from typing import Dict, Any, Optional
from datetime import datetime


@dataclass
class Response:
    """HTTP response data class."""

    status: int
    url: str
    content: Optional[str] = None
    error: Optional[str] = None
    headers: Optional[Dict[str, str]] = None
    timestamp: datetime = datetime.now()

    @property
    def is_success(self) -> bool:
        """Check if the response was successful."""
        return 200 <= self.status < 300

    @property
    def is_error(self) -> bool:
        """Check if the response was an error."""
        return self.status >= 400

    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary."""
        return {
            "status": self.status,
            "url": self.url,
            "content": self.content,
            "error": self.error,
            "headers": self.headers,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Response":
        """Create response from dictionary."""
        return cls(
            status=data["status"],
            url=data["url"],
            content=data.get("content"),
            error=data.get("error"),
            headers=data.get("headers"),
            timestamp=datetime.fromisoformat(data["timestamp"]),
        )
