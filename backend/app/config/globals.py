"""
Global state management for the application.
This module provides centralized access to global variables and functions.
"""

import logging
from typing import Optional, List, Any
import asyncio
from pathlib import Path

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Create formatter
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
console_handler.setFormatter(formatter)

# Add handler to logger
logger.addHandler(console_handler)

# Database state
_current_db_name: str = ""
_available_databases: List[str] = []

# Crawler state
_crawler_running: bool = False
_crawler_task: Optional[asyncio.Task] = None
_current_crawler: Optional[Any] = None  # Type will be CrawlerService

# Seed URLs
_seed_urls: List[str] = []


# Database state management
def get_current_db() -> str:
    """Get the current database name"""
    return _current_db_name


def set_current_db(db_name: str) -> None:
    """Set the current database name"""
    global _current_db_name
    _current_db_name = db_name
    logger.info(f"Current database set to: {db_name}")


def get_available_databases() -> List[str]:
    """Get list of available databases"""
    return _available_databases


def set_available_databases(databases: List[str]) -> None:
    """Set list of available databases"""
    global _available_databases
    _available_databases = databases
    logger.info(f"Available databases updated: {databases}")


# Crawler state management
def is_crawler_running() -> bool:
    """Check if crawler is running"""
    return _crawler_running


def set_crawler_running(running: bool) -> None:
    """Set crawler running state"""
    global _crawler_running
    _crawler_running = running
    logger.info(f"Crawler running state set to: {running}")


def get_crawler_task() -> Optional[asyncio.Task]:
    """Get current crawler task"""
    return _crawler_task


def set_crawler_task(task: Optional[asyncio.Task]) -> None:
    """Set current crawler task"""
    global _crawler_task
    _crawler_task = task
    logger.info("Crawler task updated")


def get_current_crawler() -> Optional[Any]:  # Type will be CrawlerService
    """Get current crawler instance"""
    return _current_crawler


def set_current_crawler(crawler: Optional[Any]) -> None:  # Type will be CrawlerService
    """Set current crawler instance"""
    global _current_crawler
    _current_crawler = crawler
    logger.info("Crawler instance updated")


# Seed URLs management
def get_seed_urls() -> List[str]:
    """Get current seed URLs"""
    return _seed_urls


def set_seed_urls(urls: List[str]) -> None:
    """Set seed URLs"""
    global _seed_urls
    _seed_urls = urls
    logger.info(f"Seed URLs updated: {urls}")
