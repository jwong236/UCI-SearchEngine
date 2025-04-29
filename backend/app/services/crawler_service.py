import asyncio
import httpx
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from typing import List, Optional, Set
import logging
import json
import numpy as np
from ..models.crawler import URL, URLRelationship, DomainRateLimit, CrawlStatistics
from .tokenizer_service import tokenize, get_token_frequencies

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
        # Initialize vocabulary and document frequency tracking
        self.vocabulary = set()
        self.document_frequency = {}

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

    def _extract_text_content(self, soup: BeautifulSoup) -> str:
        """Extract clean text content from HTML."""
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()

        # Get text and clean it
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = " ".join(chunk for chunk in chunks if chunk)
        return text

    def _extract_meta_description(self, soup: BeautifulSoup) -> str:
        """Extract meta description from HTML."""
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc and meta_desc.get("content"):
            return meta_desc["content"]
        return ""

    def _extract_headings(self, soup: BeautifulSoup) -> str:
        """Extract important headings from HTML."""
        headings = []
        for tag in ["h1", "h2", "h3"]:
            for heading in soup.find_all(tag):
                if heading.get_text().strip():
                    headings.append({"level": tag, "text": heading.get_text().strip()})
        return json.dumps(headings)

    def _calculate_document_vector(self, text: str) -> bytes:
        """Calculate and store TF-IDF vector for the document."""
        # Tokenize and get frequencies
        tokens = tokenize(text)
        term_frequencies = get_token_frequencies(tokens)

        # Update vocabulary and document frequency
        self.vocabulary.update(term_frequencies.keys())
        for term in term_frequencies:
            self.document_frequency[term] = self.document_frequency.get(term, 0) + 1

        # Calculate TF-IDF vector
        total_docs = self.db.query(URL).count() + 1  # +1 for current document
        vector = []
        for term in sorted(self.vocabulary):
            tf = term_frequencies.get(term, 0) / len(tokens) if tokens else 0
            idf = np.log(total_docs / (self.document_frequency.get(term, 0) + 1))
            vector.append(tf * idf)

        # Normalize vector
        vector = np.array(vector)
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm

        return vector.tobytes()

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

            # Extract all required content
            title = soup.title.string if soup.title else ""
            text_content = self._extract_text_content(soup)
            meta_description = self._extract_meta_description(soup)
            important_headings = self._extract_headings(soup)
            document_vector = self._calculate_document_vector(text_content)
            word_count = len(tokenize(text_content))

            if not existing_url:
                url_record = URL(
                    url=url,
                    domain=urlparse(url).netloc,
                    status_code=response.status_code,
                    last_crawled=datetime.now(timezone.utc),
                    is_completed=True,
                    title=title,
                    text_content=text_content,
                    document_vector=document_vector,
                    meta_description=meta_description,
                    important_headings=important_headings,
                    word_count=word_count,
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
                url_record.text_content = text_content
                url_record.document_vector = document_vector
                url_record.meta_description = meta_description
                url_record.important_headings = important_headings
                url_record.word_count = word_count
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
                existing_url.is_completed = True
                self.db.commit()
            else:
                url_record = URL(
                    url=url,
                    domain=urlparse(url).netloc,
                    status_code=500,
                    last_crawled=datetime.now(timezone.utc),
                    is_completed=True,
                )
                self.db.add(url_record)
                self.db.commit()

            self.mark_url_complete(url)

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
