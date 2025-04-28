import asyncio
import httpx
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from typing import List, Optional, Set
import logging
from ..models.crawler import URL, URLRelationship, DomainRateLimit, CrawlStatistics

# Get logger for this module
logger = logging.getLogger(__name__)


class CrawlerService:
    def __init__(self, db: Session):
        self.db = db
        self.to_be_downloaded: List[str] = []
        self.completed: Set[str] = set()
        self.client = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            verify=False,  # Disable SSL verification
            headers={"User-Agent": "UCI Search Engine Crawler - Educational Project"},
        )

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    def add_url(self, url: str) -> None:
        """Add a URL to the frontier if it hasn't been crawled."""
        url = self._normalize_url(url)
        if url not in self.completed and url not in self.to_be_downloaded:
            self.to_be_downloaded.append(url)
            logger.info(f"Added URL to frontier: {url}")

    def get_next_url(self) -> Optional[str]:
        """Get the next URL to crawl from the frontier."""
        try:
            return self.to_be_downloaded.pop()
        except IndexError:
            return None

    def mark_url_complete(self, url: str) -> None:
        """Mark a URL as completed."""
        url = self._normalize_url(url)
        self.completed.add(url)
        logger.info(f"Marked URL as complete: {url}")

    def _normalize_url(self, url: str) -> str:
        """Normalize URL by removing fragments and trailing slashes."""
        parsed = urlparse(url)
        normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        if parsed.query:
            normalized += f"?{parsed.query}"
        return normalized.rstrip("/")

    async def process_url(self, url: str) -> None:
        """Process a single URL: fetch, parse, and store its content."""
        logger.info(f"Starting to process URL: {url}")
        existing_url = None
        try:
            existing_url = self.db.query(URL).filter(URL.url == url).first()
            if existing_url and existing_url.is_completed:
                logger.info(f"URL already processed: {url}")
                return

            await self._check_rate_limit(url)
            logger.info(f"Fetching URL: {url}")
            response = await self.client.get(url)
            soup = BeautifulSoup(response.text, "html.parser")
            title = soup.title.string if soup.title else ""

            if not existing_url:
                url_record = URL(
                    url=url,
                    domain=urlparse(url).netloc,
                    status_code=response.status_code,
                    last_crawled=datetime.now(timezone.utc),
                    is_completed=True,
                    title=title,
                    content=response.text,
                )
                self.db.add(url_record)
                logger.info(f"Added new URL record: {url}")
            else:
                url_record = existing_url
                url_record.domain = urlparse(url).netloc
                url_record.status_code = response.status_code
                url_record.last_crawled = datetime.now(timezone.utc)
                url_record.is_completed = True
                url_record.title = title
                url_record.content = response.text
                logger.info(f"Updated existing URL record: {url}")

            if response.status_code == 200:
                await self._process_links(url_record, soup)

            self._update_statistics(url_record)
            self.db.commit()
            self.mark_url_complete(url)
            logger.info(f"Successfully processed URL: {url}")

        except Exception as e:
            logger.error(f"Error processing URL {url}: {str(e)}")
            self.db.rollback()
            if existing_url:
                existing_url.status_code = 500
                existing_url.last_crawled = datetime.now(timezone.utc)
                existing_url.is_completed = True  # Mark as completed even if it failed
                self.db.commit()
            else:
                # Create a new URL record for failed URLs
                url_record = URL(
                    url=url,
                    domain=urlparse(url).netloc,
                    status_code=500,
                    last_crawled=datetime.now(timezone.utc),
                    is_completed=True,
                )
                self.db.add(url_record)
                self.db.commit()

            self.mark_url_complete(url)  # Mark as completed in memory too

    async def _check_rate_limit(self, url: str) -> None:
        """Implement rate limiting per domain."""
        domain = urlparse(url).netloc
        rate_limit = (
            self.db.query(DomainRateLimit)
            .filter(DomainRateLimit.domain == domain)
            .first()
        )

        if not rate_limit:
            rate_limit = DomainRateLimit(
                domain=domain,
                last_request=datetime.now(timezone.utc),
                delay_seconds=1.0,
            )
            self.db.add(rate_limit)
            logger.info(f"Created rate limit for domain: {domain}")
        else:
            time_since_last = (
                datetime.now(timezone.utc)
                - rate_limit.last_request.replace(tzinfo=timezone.utc)
            ).total_seconds()
            if time_since_last < rate_limit.delay_seconds:
                await asyncio.sleep(rate_limit.delay_seconds - time_since_last)
                logger.info(
                    f"Rate limited for domain {domain}, waited {rate_limit.delay_seconds - time_since_last}s"
                )

            rate_limit.last_request = datetime.now(timezone.utc)

        self.db.commit()

    async def _process_links(self, source_url: URL, soup: BeautifulSoup) -> None:
        """Extract and store links from the page."""
        links_processed = 0
        for link in soup.find_all("a", href=True):
            href = link["href"]
            absolute_url = urljoin(source_url.url, href)

            if not self._is_valid_uci_url(absolute_url):
                continue

            # Check if URL already exists in database
            target_url = self.db.query(URL).filter(URL.url == absolute_url).first()
            if not target_url:
                target_url = URL(url=absolute_url, domain=urlparse(absolute_url).netloc)
                self.db.add(target_url)
                self.db.flush()  # Get the ID without committing

            # Check if relationship already exists
            relationship = (
                self.db.query(URLRelationship)
                .filter(
                    URLRelationship.source_url_id == source_url.id,
                    URLRelationship.target_url_id == target_url.id,
                )
                .first()
            )

            if not relationship:
                relationship = URLRelationship(
                    source_url=source_url, target_url=target_url
                )
                self.db.add(relationship)
                links_processed += 1

            # Only add to frontier if URL is not completed
            if not target_url.is_completed:
                self.add_url(absolute_url)

        logger.info(f"Processed {links_processed} links from {source_url.url}")

    def _is_valid_uci_url(self, url: str) -> bool:
        """Check if URL is a valid UCI URL to crawl."""
        parsed = urlparse(url)
        valid_domains = {
            "ics.uci.edu",
            "cs.uci.edu",
            "informatics.uci.edu",
            "stat.uci.edu",
        }
        return any(domain in parsed.netloc for domain in valid_domains)

    def _update_statistics(self, url: URL) -> None:
        """Update crawl statistics."""
        stats = (
            self.db.query(CrawlStatistics).order_by(CrawlStatistics.id.desc()).first()
        )

        if not stats:
            stats = CrawlStatistics(
                urls_crawled=0, urls_failed=0, total_words=0, unique_domains=0
            )
            self.db.add(stats)
            logger.info("Created new crawl statistics record")

        stats.urls_crawled = (stats.urls_crawled or 0) + 1
        if url.status_code != 200:
            stats.urls_failed = (stats.urls_failed or 0) + 1

        unique_domains = self.db.query(URL.domain).distinct().count()
        stats.unique_domains = unique_domains
        self.db.commit()
        logger.info(
            f"Updated statistics: {stats.urls_crawled} crawled, {stats.urls_failed} failed, {stats.unique_domains} domains"
        )
