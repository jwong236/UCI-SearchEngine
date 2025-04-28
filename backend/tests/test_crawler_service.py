import pytest
import asyncio
from datetime import datetime, timezone
from unittest.mock import Mock, patch
from bs4 import BeautifulSoup
from app.services.crawler_service import CrawlerService
from app.models.crawler import URL, URLRelationship, DomainRateLimit, CrawlStatistics


@pytest.fixture
def mock_db():
    return Mock()


@pytest.fixture
def crawler_service(mock_db):
    return CrawlerService(mock_db)


@pytest.fixture
def sample_html():
    return """
    <html>
        <head><title>Test Page</title></head>
        <body>
            <a href="https://ics.uci.edu/page1">Link 1</a>
            <a href="https://cs.uci.edu/page2">Link 2</a>
            <a href="https://example.com">External Link</a>
        </body>
    </html>
    """


@pytest.mark.asyncio
async def test_process_url_success(crawler_service, mock_db, sample_html):
    url = "https://ics.uci.edu/test"
    mock_db.query.return_value.filter.return_value.first.return_value = None

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.text = sample_html

        await crawler_service.process_url(url)

        mock_db.add.assert_called()
        mock_db.commit.assert_called()


@pytest.mark.asyncio
async def test_process_url_already_crawled(crawler_service, mock_db):
    url = "https://ics.uci.edu/test"
    existing_url = Mock(spec=URL)
    existing_url.is_completed = True
    mock_db.query.return_value.filter.return_value.first.return_value = existing_url

    await crawler_service.process_url(url)

    mock_db.add.assert_not_called()
    mock_db.commit.assert_not_called()


@pytest.mark.asyncio
async def test_check_rate_limit(crawler_service, mock_db):
    url = "https://ics.uci.edu/test"
    mock_db.query.return_value.filter.return_value.first.return_value = None

    await crawler_service._check_rate_limit(url)

    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_process_links(crawler_service, mock_db, sample_html):
    # Create a real URL object instead of a mock
    source_url = URL(id=1, url="https://ics.uci.edu/source")
    soup = BeautifulSoup(sample_html, "html.parser")

    # Mock the database queries
    mock_db.query.return_value.filter.return_value.first.return_value = None

    # Patch the relationship creation
    with patch("app.models.crawler.URLRelationship") as mock_relationship:
        await crawler_service._process_links(source_url, soup)
        assert mock_db.add.call_count >= 2


def test_is_valid_uci_url(crawler_service):
    valid_urls = [
        "https://ics.uci.edu/page",
        "https://cs.uci.edu/page",
        "https://informatics.uci.edu/page",
        "https://stat.uci.edu/page",
    ]
    invalid_urls = ["https://example.com", "https://uci.edu", "https://other.uci.edu"]

    for url in valid_urls:
        assert crawler_service._is_valid_uci_url(url)

    for url in invalid_urls:
        assert not crawler_service._is_valid_uci_url(url)


def test_update_statistics(crawler_service, mock_db):
    url = Mock(spec=URL)
    url.status_code = 200

    # Create a real CrawlStatistics object with initialized values
    stats = CrawlStatistics(urls_crawled=0, urls_failed=0, unique_domains=0)
    mock_db.query.return_value.order_by.return_value.first.return_value = stats
    mock_db.query.return_value.distinct.return_value.count.return_value = 5

    crawler_service._update_statistics(url)

    assert stats.urls_crawled == 1
    assert stats.urls_failed == 0
    assert stats.unique_domains == 5
    mock_db.commit.assert_called_once()
