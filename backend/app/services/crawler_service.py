import asyncio
import httpx
import os
import shelve
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from typing import List, Optional
from ..models.crawler import URL, URLRelationship, DomainRateLimit, CrawlStatistics


class CrawlerService:
    def __init__(self, db: Session, save_file: str = "crawler_state.db"):
        self.db = db
        self.save_file = save_file
        self.client = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers={"User-Agent": "UCI Search Engine Crawler - Educational Project"},
        )
        self._load_state()

    def _load_state(self) -> None:
        """Load crawler state from disk."""
        if os.path.exists(self.save_file):
            self.save = shelve.open(self.save_file)
        else:
            self.save = shelve.open(self.save_file)
            self.save["to_be_downloaded"] = []
            self.save["completed"] = set()

    def _save_state(self) -> None:
        """Save crawler state to disk."""
        self.save.sync()

    def add_url(self, url: str) -> None:
        """Add a URL to the frontier if it hasn't been crawled."""
        url = self._normalize_url(url)
        if url not in self.save["completed"]:
            if url not in self.save["to_be_downloaded"]:
                self.save["to_be_downloaded"].append(url)
                self._save_state()

    def get_next_url(self) -> Optional[str]:
        """Get the next URL to crawl from the frontier."""
        try:
            return self.save["to_be_downloaded"].pop()
        except IndexError:
            return None

    def mark_url_complete(self, url: str) -> None:
        """Mark a URL as completed."""
        url = self._normalize_url(url)
        self.save["completed"].add(url)
        self._save_state()

    def _normalize_url(self, url: str) -> str:
        """Normalize URL by removing fragments and trailing slashes."""
        parsed = urlparse(url)
        normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        if parsed.query:
            normalized += f"?{parsed.query}"
        return normalized.rstrip("/")

    async def process_url(self, url: str) -> None:
        """Process a single URL: fetch, parse, and store its content."""
        try:
            existing_url = self.db.query(URL).filter(URL.url == url).first()
            if existing_url and existing_url.is_completed:
                return

            await self._check_rate_limit(url)
            response = await self.client.get(url)
            soup = BeautifulSoup(response.text, "html.parser")
            title = soup.title.string if soup.title else ""

            url_record = existing_url or URL(url=url)
            url_record.domain = urlparse(url).netloc
            url_record.status_code = response.status_code
            url_record.last_crawled = datetime.now(timezone.utc)
            url_record.is_completed = True
            url_record.title = title
            url_record.content = response.text

            if not existing_url:
                self.db.add(url_record)

            if response.status_code == 200:
                await self._process_links(url_record, soup)

            self._update_statistics(url_record)
            self.db.commit()
            self.mark_url_complete(url)

        except Exception as e:
            self.db.rollback()
            if existing_url:
                existing_url.status_code = 500
                existing_url.last_crawled = datetime.now(timezone.utc)
                self.db.commit()

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
        else:
            time_since_last = (
                datetime.now(timezone.utc) - rate_limit.last_request
            ).total_seconds()
            if time_since_last < rate_limit.delay_seconds:
                await asyncio.sleep(rate_limit.delay_seconds - time_since_last)

            rate_limit.last_request = datetime.now(timezone.utc)

        self.db.commit()

    async def _process_links(self, source_url: URL, soup: BeautifulSoup) -> None:
        """Extract and store links from the page."""
        for link in soup.find_all("a", href=True):
            href = link["href"]
            absolute_url = urljoin(source_url.url, href)

            if not self._is_valid_uci_url(absolute_url):
                continue

            target_url = self.db.query(URL).filter(URL.url == absolute_url).first()
            if not target_url:
                target_url = URL(url=absolute_url, domain=urlparse(absolute_url).netloc)
                self.db.add(target_url)

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

            self.add_url(absolute_url)

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
            stats = CrawlStatistics()
            self.db.add(stats)

        stats.urls_crawled += 1
        if url.status_code != 200:
            stats.urls_failed += 1

        unique_domains = self.db.query(URL.domain).distinct().count()
        stats.unique_domains = unique_domains
        self.db.commit()

    async def crawl(self, seed_urls: List[str]) -> None:
        """Start crawling from seed URLs."""
        for url in seed_urls:
            self.add_url(url)

        while True:
            url = self.get_next_url()
            if not url:
                break
            await self.process_url(url)
