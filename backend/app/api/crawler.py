"""
Crawler service for managing the web crawler.
"""

import asyncio
import httpx
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from typing import Set, List, Dict, Optional
from ..config.globals import (
    logger,
    get_current_db,
    is_crawler_running,
    set_crawler_running,
    get_crawler_task,
    set_crawler_task,
    get_current_crawler,
    set_current_crawler,
    get_seed_urls,
    set_seed_urls,
)
from ..database.connection import get_db
from ..database.models import (
    Document,
    DocumentRelationship,
    DomainRateLimit,
    CrawlStatistics,
    Statistics,
    Term,
    InvertedIndex,
    CrawlerState,
)
from .websocket_utils import broadcast_log
from ..config.settings import settings


class CrawlerService:
    def __init__(self):
        self._running = False
        self._task = None
        self._seed_urls = []
        self.to_visit = []
        self.visited = set()
        self.failed = set()
        self.stats = CrawlStatistics(
            urls_crawled=0,
            urls_failed=0,
            unique_domains=0,
            start_time=datetime.now(timezone.utc),
        )
        self.client = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            verify=False,
            headers={"User-Agent": "UCI Search Engine Crawler - Educational Project"},
        )

    async def start(self, seed_urls: Optional[List[str]] = None) -> None:
        """Start the crawler with optional seed URLs"""
        if is_crawler_running():
            logger.warning("Crawler is already running")
            return

        if seed_urls:
            set_seed_urls(seed_urls)
        else:
            seed_urls = get_seed_urls()

        if not seed_urls:
            logger.error("No seed URLs provided")
            return

        set_crawler_running(True)
        self._task = asyncio.create_task(self._crawl(seed_urls))
        set_crawler_task(self._task)
        set_current_crawler(self)
        logger.info(f"Started crawler with seed URLs: {seed_urls}")

    async def stop(self) -> None:
        """Stop the crawler"""
        if not is_crawler_running():
            logger.warning("Crawler is not running")
            return

        set_crawler_running(False)
        task = get_crawler_task()
        if task:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        set_crawler_task(None)
        set_current_crawler(None)
        logger.info("Stopped crawler")

    async def _crawl(self, seed_urls: List[str]) -> None:
        """Main crawling loop"""
        try:
            async with get_db() as db:
                # Initialize crawler state
                state = CrawlerState(
                    current_url=seed_urls[0],
                    urls_visited=0,
                    urls_failed=0,
                    urls_queued=len(seed_urls),
                )
                db.add(state)
                await db.commit()

                # Main crawling loop
                while is_crawler_running() and seed_urls:
                    url = seed_urls.pop(0)
                    try:
                        # TODO: Implement actual crawling logic
                        await asyncio.sleep(1)  # Simulate work
                        state.urls_visited += 1
                        await db.commit()
                        logger.info(f"Visited URL: {url}")
                    except Exception as e:
                        state.urls_failed += 1
                        await db.commit()
                        logger.error(f"Failed to crawl {url}: {str(e)}")

        except Exception as e:
            logger.error(f"Crawler error: {str(e)}")
        finally:
            set_crawler_running(False)
            set_crawler_task(None)
            set_current_crawler(None)

    async def close(self):
        await self.client.aclose()

    def _normalize_url(self, url: str) -> str:
        parsed = urlparse(url)
        normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        if parsed.query:
            normalized += f"?{parsed.query}"
        return normalized.rstrip("/")

    def _is_valid_uci_url(self, url: str) -> bool:
        parsed = urlparse(url)
        return any(
            domain in parsed.netloc
            for domain in [
                "uci.edu",
                "ics.uci.edu",
                "cs.uci.edu",
                "informatics.uci.edu",
                "stat.uci.edu",
            ]
        )

    async def _check_rate_limit(self, url: str) -> None:
        domain = urlparse(url).netloc
        rate_limit = (
            self.db.query(DomainRateLimit)
            .filter(DomainRateLimit.domain == domain)
            .first()
        )

        if not rate_limit:
            rate_limit = DomainRateLimit(domain=domain)
            self.db.add(rate_limit)
            self.db.commit()

        if rate_limit.last_request:
            delay = rate_limit.delay_seconds
            await asyncio.sleep(delay)

        rate_limit.last_request = datetime.now(timezone.utc)
        self.db.commit()

    def _extract_text_content(self, soup: BeautifulSoup) -> str:
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        return " ".join(chunk for chunk in chunks if chunk)

    def _tokenize(self, text: str) -> List[str]:
        return [word.lower() for word in re.findall(r"\w+", text)]

    def _build_inverted_index(self, doc_id: int, text: str) -> None:
        tokens = self._tokenize(text)

        for position, token in enumerate(tokens):
            term = self.db.query(Term).filter(Term.term == token).first()
            if not term:
                term = Term(term=token)
                self.db.add(term)
                self.db.commit()

            index_entry = InvertedIndex(
                term_id=term.id, document_id=doc_id, position=position
            )
            self.db.add(index_entry)

        self.db.commit()

    def _update_statistics(self, success: bool = True):
        if success:
            self.stats.urls_crawled += 1
        else:
            self.stats.urls_failed += 1

        self.stats.unique_domains = len(
            set(doc.url.split("/")[2] for doc in self.db.query(Document).all())
        )
        self.db.commit()

    def _reconstruct_queue(self):
        """Reconstruct the queue from database relationships"""
        # Get all documents that have been crawled (have outgoing links)
        crawled_docs = (
            self.db.query(Document)
            .join(
                DocumentRelationship,
                Document.id == DocumentRelationship.source_document_id,
            )
            .distinct()
            .all()
        )

        # Get all documents that have been discovered (have incoming links)
        discovered_docs = (
            self.db.query(Document)
            .join(
                DocumentRelationship,
                Document.id == DocumentRelationship.target_document_id,
            )
            .distinct()
            .all()
        )

        # URLs that have been discovered but not crawled
        discovered_urls = {doc.url for doc in discovered_docs}
        crawled_urls = {doc.url for doc in crawled_docs}

        # The queue is discovered URLs minus crawled URLs
        self.to_visit = list(discovered_urls - crawled_urls)
        self.visited = crawled_urls

        return len(self.to_visit)
