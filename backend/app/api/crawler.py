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
from sqlalchemy import select, text
from typing import List, Optional
from ..config.globals import (
    logger,
    is_crawler_running,
    set_crawler_running,
    get_crawler_task,
    set_crawler_task,
    set_current_crawler,
    get_seed_urls,
    set_seed_urls,
)
from ..database.connection import get_db
from ..database.models import (
    Document,
    DocumentRelationship,
    CrawlStatistics,
    Term,
    InvertedIndex,
    CrawlerState,
)
from .websocket_utils import broadcast_log
from ..config.settings import settings
from ..utils.rate_limiter import RateLimiter

logging.getLogger("sqlalchemy.engine").setLevel(logging.ERROR)
logging.getLogger("sqlalchemy.pool").setLevel(logging.ERROR)
logging.getLogger("sqlalchemy.dialects").setLevel(logging.ERROR)
logging.getLogger("sqlalchemy").setLevel(logging.ERROR)

for logger_name in [
    "sqlalchemy",
    "sqlalchemy.engine",
    "sqlalchemy.pool",
    "sqlalchemy.dialects",
    "sqlalchemy.orm",
]:
    logging.getLogger(logger_name).setLevel(logging.CRITICAL)


class CrawlerService:
    def __init__(self):
        self._running = False
        self._task = None
        self._seed_urls = []
        self.to_visit = []
        self.visited = set()
        self.failed = set()
        self.stats = None
        self.rate_limiter = RateLimiter(requests_per_second=1.0)

        self.client = httpx.AsyncClient(
            timeout=60.0,
            follow_redirects=True,
            verify=False,
            headers={
                "User-Agent": "UCI Search Engine Crawler - Educational Project",
                "Accept": "text/html,application/xhtml+xml,application/xml",
                "Accept-Language": "en-US,en;q=0.9",
            },
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
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

        self.to_visit = []
        self.visited = set()
        self.failed = set()

        async with get_db() as db:
            existing_docs = await db.execute(
                select(Document).where(Document.is_crawled == True)
            )
            existing_docs = existing_docs.scalars().all()

            for doc in existing_docs:
                if doc.crawl_failed:
                    self.failed.add(doc.url)
                else:
                    self.visited.add(doc.url)

        self.to_visit.extend(seed_urls)
        await broadcast_log(f"Initialized crawler with {len(seed_urls)} seed URLs")

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
                # Initialize statistics
                self.stats = CrawlStatistics(
                    urls_crawled=0,
                    urls_failed=0,
                    unique_domains=0,
                    timestamp=datetime.now(timezone.utc),
                )
                db.add(self.stats)

                # Initialize or update crawler state
                state = CrawlerState(
                    current_url=seed_urls[0] if seed_urls else None,
                    urls_visited=len(self.visited),
                    urls_failed=len(self.failed),
                    urls_queued=len(self.to_visit),
                    updated_at=datetime.now(timezone.utc),
                )
                db.add(state)
                await db.commit()

                # Initialize queue with seed URLs if empty
                if not self.to_visit:
                    self.to_visit.extend(seed_urls)
                    await broadcast_log(
                        f"Added {len(seed_urls)} seed URLs to the queue"
                    )

                await broadcast_log(
                    f"Starting crawl with {len(self.to_visit)} URLs in queue"
                )
                await broadcast_log(
                    f"Queue content: {', '.join(self.to_visit[:3])}{'...' if len(self.to_visit) > 3 else ''}"
                )

                while self.to_visit and is_crawler_running():
                    url = self.to_visit.pop(0)
                    await broadcast_log(f"Processing URL: {url}")

                    if url in self.visited or url in self.failed:
                        await broadcast_log(
                            f"Skipping already visited/failed URL: {url}"
                        )
                        continue

                    try:
                        await broadcast_log(f"Crawling: {url}")

                        domain = urlparse(url).netloc
                        await self.rate_limiter.async_wait_if_needed(domain)

                        start_time = datetime.now(timezone.utc)
                        await broadcast_log(f"Sending request to: {url}")

                        response = await self.client.get(url)
                        response.raise_for_status()

                        end_time = datetime.now(timezone.utc)
                        duration = (end_time - start_time).total_seconds()
                        await broadcast_log(
                            f"Received response from {url} in {duration:.2f} seconds"
                        )

                        soup = BeautifulSoup(response.text, "html.parser")
                        title = soup.title.string if soup.title else url
                        content = soup.get_text()

                        await broadcast_log(
                            f"Parsed content from {url}, title: {title[:30]}{'...' if len(title) > 30 else ''}"
                        )

                        # Update or create document
                        existing_doc = await self._document_exists(db, url)
                        if existing_doc:
                            existing_doc.title = title
                            existing_doc.content = content
                            existing_doc.last_crawled_at = datetime.now(timezone.utc)
                            existing_doc.is_crawled = True
                            existing_doc.crawl_failed = False
                            existing_doc.error_message = None
                            doc = existing_doc
                        else:
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

                        await db.flush()
                        await broadcast_log(f"Added document to database, ID: {doc.id}")

                        # Extract and process new URLs
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
                                and normalized_url not in self.to_visit
                                and normalized_url != url
                                and self._is_valid_uci_url(normalized_url)
                            ):
                                new_urls.add(normalized_url)

                        await broadcast_log(f"Found {len(new_urls)} new URLs on {url}")

                        # Process new URLs and create relationships
                        for new_url in new_urls:
                            if new_url not in self.to_visit:
                                self.to_visit.append(new_url)

                                existing_doc = await self._document_exists(db, new_url)
                                if existing_doc:
                                    relationship = DocumentRelationship(
                                        source_document_id=doc.id,
                                        target_document_id=existing_doc.id,
                                    )
                                    db.add(relationship)
                                else:
                                    target_doc = Document(
                                        url=new_url,
                                        title=new_url,
                                        content="",
                                        discovered_at=datetime.now(timezone.utc),
                                        is_crawled=False,
                                        crawl_failed=False,
                                    )
                                    db.add(target_doc)
                                    await db.flush()

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
                            sample_urls = list(new_urls)[:3]
                            await broadcast_log(
                                f"Found URLs: {', '.join(sample_urls)}{'...' if len(new_urls) > 3 else ''}"
                            )

                        # Update crawler state
                        self.visited.add(url)
                        state.current_url = url
                        state.urls_visited += 1
                        state.updated_at = datetime.now(timezone.utc)

                        await self._update_statistics(True, db)
                        await db.commit()
                        await broadcast_log(f"Committed changes for {url}")

                    except Exception as e:
                        self.failed.add(url)

                        try:
                            await db.rollback()

                            # Update failed state
                            state = await db.execute(
                                select(CrawlerState)
                                .order_by(CrawlerState.id.desc())
                                .limit(1)
                            )
                            state = state.scalar_one_or_none()

                            if state:
                                state.urls_failed += 1
                                state.updated_at = datetime.now(timezone.utc)
                                await db.commit()

                            # Update document error state
                            doc = await self._document_exists(db, url)
                            if doc:
                                doc.crawl_failed = True
                                doc.error_message = str(e)
                                doc.last_crawled_at = datetime.now(timezone.utc)
                                await db.commit()

                        except Exception as recovery_error:
                            await broadcast_log(
                                f"Failed to recover from error: {str(recovery_error)}"
                            )

                        await broadcast_log(f"Failed to crawl {url}: {str(e)}")

                        try:
                            await self._update_statistics(False, db)
                            await db.commit()
                        except Exception:
                            await broadcast_log(
                                "Failed to update statistics after error"
                            )

                await broadcast_log(
                    f"Crawling complete or stopped. Visited {len(self.visited)} URLs, Failed {len(self.failed)} URLs"
                )

        except Exception as e:
            await broadcast_log(f"Crawler error: {str(e)}")
            import traceback

            await broadcast_log(f"Stack trace: {traceback.format_exc()}")
        finally:
            set_crawler_running(False)
            set_crawler_task(None)
            set_current_crawler(None)
            await self.close()
            await broadcast_log("Crawler resources have been released")

    async def close(self):
        await self.client.aclose()

    def _normalize_url(self, url: str) -> str:
        """Normalize URL by removing fragments, query parameters and trailing slashes."""
        parsed = urlparse(url)
        normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip(
            "/"
        ).lower()

        if parsed.query and (
            any(parsed.path.endswith(ext) for ext in [".php", ".aspx", ".jsp"])
            or any(param in parsed.query for param in ["id", "article", "page", "p"])
        ):
            normalized += f"?{parsed.query}"

        return normalized

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

        for token in tokens:
            term_frequencies[token] = term_frequencies.get(token, 0) + 1

        total_terms = len(tokens)

        total_docs = (await db.execute(select(Document))).scalars().all()
        total_docs = len(total_docs) or 1

        for token, frequency in term_frequencies.items():
            term = (
                await db.execute(select(Term).where(Term.term == token))
            ).scalar_one_or_none()
            if not term:
                term = Term(term=token)
                db.add(term)
                await db.commit()

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
            df = len(df) or 1
            idf = 1 + (total_docs / df)
            tf_idf = tf * idf

            index_entry = InvertedIndex(
                term_id=term.id,
                document_id=doc_id,
                term_frequency=frequency,
                tf_idf=tf_idf,
            )
            db.add(index_entry)

        await db.commit()

    async def _update_statistics(self, success: bool = True, db: AsyncSession = None):
        """Update crawler statistics with minimal logging"""
        if not db:
            async with get_db() as db:
                await self._update_statistics(success, db)
                return

        if success:
            self.stats.urls_crawled += 1
        else:
            self.stats.urls_failed += 1

        if (self.stats.urls_crawled + self.stats.urls_failed) % 10 == 0:
            domains_query = """
            SELECT COUNT(DISTINCT SUBSTR(url, INSTR(url, '://') + 3, 
                   CASE WHEN INSTR(SUBSTR(url, INSTR(url, '://') + 3), '/') = 0 
                   THEN LENGTH(SUBSTR(url, INSTR(url, '://') + 3))
                   ELSE INSTR(SUBSTR(url, INSTR(url, '://') + 3), '/') - 1 END))
            FROM documents
            """
            result = await db.execute(text(domains_query))
            self.stats.unique_domains = result.scalar() or 0

        if (self.stats.urls_crawled + self.stats.urls_failed) % 5 == 0:
            await db.commit()

    async def _reconstruct_queue(self, db: AsyncSession) -> int:
        """Reconstruct the queue from database relationships"""
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

        discovered_urls = {doc.url for doc in discovered_docs}
        crawled_urls = {doc.url for doc in crawled_docs}

        self.to_visit = list(discovered_urls - crawled_urls)
        self.visited = crawled_urls

        return len(self.to_visit)

    async def _document_exists(self, db: AsyncSession, url: str) -> Optional[Document]:
        """Check if a document with the given URL exists in the database"""
        result = await db.execute(select(Document).where(Document.url == url))
        return result.scalar_one_or_none()
