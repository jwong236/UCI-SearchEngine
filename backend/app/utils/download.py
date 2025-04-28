import httpx
from typing import Optional, Tuple, Dict, Any
from dataclasses import dataclass


@dataclass
class Response:
    """Response data class for storing download results."""

    status: int
    url: str
    content: Optional[str] = None
    error: Optional[str] = None


async def download(url: str, user_agent: str, timeout: float = 30.0) -> Response:
    """
    Download content from a URL.

    Args:
        url: URL to download
        user_agent: User agent string
        timeout: Request timeout in seconds

    Returns:
        Response object containing the download result
    """
    try:
        async with httpx.AsyncClient(
            timeout=timeout, follow_redirects=True, headers={"User-Agent": user_agent}
        ) as client:
            response = await client.get(url)
            return Response(status=response.status_code, url=url, content=response.text)
    except Exception as e:
        return Response(status=500, url=url, error=str(e))
