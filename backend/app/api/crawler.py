"""
Crawler service for managing the web crawler.
"""

import asyncio
import httpx
import re
import logging
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
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
from ..utils.rate_limiter import RateLimiter

# Configure SQLAlchemy logging to only show errors
logging.getLogger("sqlalchemy.engine").setLevel(logging.ERROR)
logging.getLogger("sqlalchemy.pool").setLevel(logging.ERROR)
logging.getLogger("sqlalchemy.dialects").setLevel(logging.ERROR)
logging.getLogger("sqlalchemy").setLevel(
    logging.ERROR
)  # Add this line to catch all SQLAlchemy logs


class CrawlerService:
    def __init__(self):
        self._running = False
        self._task = None
        self._seed_urls = []
        self.to_visit = []
        self.visited = set()
        self.failed = set()
        self.stats = None
        self.rate_limiter = RateLimiter(requests_per_second=1.0)  # 1 request per second
        self.client = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            verify=False,
            headers={"User-Agent": "UCI Search Engine Crawler - Educational Project"},
        )

    async def start(self, seed_urls: Optional[List[str]] = None) -> None:
        """Start the crawler with optional seed URLs"""
        if is_crawler_running():
            await broadcast_log("Crawler is already running")
            return

        if seed_urls:
            set_seed_urls(seed_urls)
        else:
            seed_urls = get_seed_urls()

        if not seed_urls:
            await broadcast_log("No seed URLs provided")
            return

        set_crawler_running(True)
        self._task = asyncio.create_task(self._crawl(seed_urls))
        set_crawler_task(self._task)
        set_current_crawler(self)
        await broadcast_log(f"Started crawler with seed URLs: {seed_urls}")

    async def stop(self) -> None:
        """Stop the crawler"""
        if not is_crawler_running():
            await broadcast_log("Crawler is not running")
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
        await broadcast_log("Stopped crawler")

    async def _crawl(self, seed_urls: List[str]) -> None:
        try:
            async with get_db() as db:
                self.stats = CrawlStatistics(
                    urls_crawled=0,
                    urls_failed=0,
                    unique_domains=0,
                    timestamp=datetime.now(timezone.utc),
                )
                db.add(self.stats)
                await db.commit()

                state = CrawlerState(
                    current_url=seed_urls[0] if seed_urls else None,
                    urls_visited=0,
                    urls_failed=0,
                    urls_queued=len(seed_urls),
                )
                db.add(state)
                await db.commit()

                self.to_visit.extend(seed_urls)
                await broadcast_log(f"Starting crawl with {len(seed_urls)} seed URLs")

                while self.to_visit and is_crawler_running():
                    url = self.to_visit.pop(0)
                    if url in self.visited or url in self.failed:
                        continue

                    try:
                        await broadcast_log(f"Crawling: {url}")
                        domain = urlparse(url).netloc
                        await self.rate_limiter.async_wait_if_needed(domain)
                        response = await self.client.get(url)
                        response.raise_for_status()

                        soup = BeautifulSoup(response.text, "html.parser")
                        title = soup.title.string if soup.title else url
                        content = soup.get_text()

                        doc = Document(
                            url=url,
                            title=title,
                            content=content,
                            last_crawled_at=datetime.now(timezone.utc),
                            is_crawled=True,
                            crawl_failed=False,
                            error_message=None,
                        )
                        db.add(doc)
                        await db.commit()

                        # Extract and normalize links
                        new_urls = set()
                        for link in soup.find_all("a", href=True):
                            href = link["href"]
                            if href.startswith("#") or href.startswith("mailto:"):
                                continue
                            full_url = urljoin(url, href)
                            normalized_url = self._normalize_url(full_url)
                            if (
                                normalized_url not in self.visited
                                and normalized_url not in self.failed
                            ):
                                new_urls.add(normalized_url)

                        # Add new URLs to queue
                        for new_url in new_urls:
                            if new_url not in self.to_visit:
                                self.to_visit.append(new_url)
                                target_doc = Document(
                                    url=new_url,
                                    title=new_url,
                                    content="",
                                    discovered_at=datetime.now(timezone.utc),
                                    is_crawled=False,
                                    crawl_failed=False,
                                )
                                db.add(target_doc)
                                await db.commit()

                                relationship = DocumentRelationship(
                                    source_document_id=doc.id,
                                    target_document_id=target_doc.id,
                                )
                                db.add(relationship)
                                state.urls_queued += 1

                        await broadcast_log(
                            f"Crawled: {url} | Queue: {len(self.to_visit)} | New URLs: {len(new_urls)}"
                        )
                        if new_urls:
                            await broadcast_log(
                                f"Found URLs: {', '.join(new_urls[:3])}{'...' if len(new_urls) > 3 else ''}"
                            )

                        self.visited.add(url)
                        state.current_url = url
                        state.urls_visited += 1
                        state.updated_at = datetime.now(timezone.utc)
                        await self._update_statistics(True, db)
                        await db.commit()

                    except Exception as e:
                        self.failed.add(url)
                        state.urls_failed += 1
                        await self._update_statistics(False, db)
                        await db.commit()
                        await broadcast_log(f"Failed to crawl {url}: {str(e)}")

        except Exception as e:
            await broadcast_log(f"Crawler error: {str(e)}")
        finally:
            set_crawler_running(False)
            set_crawler_task(None)
            set_current_crawler(None)
            await self.close()

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

    def _extract_text_content(self, soup: BeautifulSoup) -> str:
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        return " ".join(chunk for chunk in chunks if chunk)

    def _tokenize(self, text: str) -> List[str]:
        return [word.lower() for word in re.findall(r"\w+", text)]

    async def _build_inverted_index(
        self, doc_id: int, text: str, db: AsyncSession
    ) -> None:
        tokens = self._tokenize(text)
        term_frequencies = {}

        # Count term frequencies
        for token in tokens:
            term_frequencies[token] = term_frequencies.get(token, 0) + 1

        # Calculate total terms for TF-IDF
        total_terms = len(tokens)

        # Get total documents for IDF calculation
        total_docs = (await db.execute(select(Document))).scalars().all()
        total_docs = len(total_docs) or 1  # Avoid division by zero

        for token, frequency in term_frequencies.items():
            # Get or create term
            term = (
                await db.execute(select(Term).where(Term.term == token))
            ).scalar_one_or_none()
            if not term:
                term = Term(term=token)
                db.add(term)
                await db.commit()

            # Calculate TF-IDF
            tf = frequency / total_terms
            df = (
                (
                    await db.execute(
                        select(InvertedIndex).where(InvertedIndex.term_id == term.id)
                    )
                )
                .scalars()
                .all()
            )
            df = len(df) or 1  # Avoid division by zero
            idf = 1 + (total_docs / df)
            tf_idf = tf * idf

            # Create or update inverted index entry
            index_entry = InvertedIndex(
                term_id=term.id,
                document_id=doc_id,
                term_frequency=frequency,
                tf_idf=tf_idf,
            )
            db.add(index_entry)

        await db.commit()

    async def _update_statistics(self, success: bool = True, db: AsyncSession = None):
        if not db:
            async with get_db() as db:
                await self._update_statistics(success, db)
            return

        if success:
            self.stats.urls_crawled += 1
        else:
            self.stats.urls_failed += 1

        self.stats.unique_domains = len(
            set(
                doc.url.split("/")[2]
                for doc in (await db.execute(select(Document))).scalars().all()
            )
        )
        await db.commit()

    async def _reconstruct_queue(self, db: AsyncSession) -> int:
        """Reconstruct the queue from database relationships"""
        # Get all documents that have been crawled (have outgoing links)
        crawled_docs = (
            (
                await db.execute(
                    select(Document)
                    .join(
                        DocumentRelationship,
                        Document.id == DocumentRelationship.source_document_id,
                    )
                    .distinct()
                )
            )
            .scalars()
            .all()
        )

        # Get all documents that have been discovered (have incoming links)
        discovered_docs = (
            (
                await db.execute(
                    select(Document)
                    .join(
                        DocumentRelationship,
                        Document.id == DocumentRelationship.target_document_id,
                    )
                    .distinct()
                )
            )
            .scalars()
            .all()
        )

        # URLs that have been discovered but not crawled
        discovered_urls = {doc.url for doc in discovered_docs}
        crawled_urls = {doc.url for doc in crawled_docs}

        # The queue is discovered URLs minus crawled URLs
        self.to_visit = list(discovered_urls - crawled_urls)
        self.visited = crawled_urls

        return len(self.to_visit)
