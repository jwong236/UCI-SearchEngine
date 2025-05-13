"""
Database connection management
"""

import logging
import os
import shutil
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import Session
from sqlalchemy.ext.declarative import declarative_base
from typing import Optional, AsyncGenerator
from datetime import datetime
from contextlib import asynccontextmanager
from ..config.globals import (
    logger,
    get_current_db,
    set_current_db,
    get_available_databases,
    set_available_databases,
)
from ..config.settings import settings
from .models import (
    Base,
    Document,
    Term,
    InvertedIndex,
    CrawlerState,
)  # Import Base and models

# Global engine and session factory
_engine: Optional[create_async_engine] = None
_session_factory: Optional[async_sessionmaker] = None


def get_db_path(db_name: str = settings.DEFAULT_DB_NAME) -> str:
    """Get the full path to a database file"""
    # Ensure the data directory exists
    os.makedirs(settings.DB_DIR, exist_ok=True)
    return os.path.join(settings.DB_DIR, f"{db_name}.sqlite")


async def setup_engine(db_name: str = get_current_db()) -> None:
    """Set up the SQLAlchemy engine for the specified database"""
    global _engine
    if _engine is not None:
        await _engine.dispose()

    # Ensure the database directory exists
    os.makedirs(settings.DB_DIR, exist_ok=True)

    # Create the database URL with the full path
    db_path = get_db_path(db_name)
    db_url = f"sqlite+aiosqlite:///{db_path}"

    _engine = create_async_engine(
        db_url, echo=True, future=True, connect_args={"check_same_thread": False}
    )
    logger.info(f"Set up engine for database: {db_name}")


async def setup_session_factory(db_name: str = get_current_db()) -> None:
    """Set up the SQLAlchemy session factory"""
    global _session_factory, _engine
    if _engine is None:
        await setup_engine(db_name)
    _session_factory = async_sessionmaker(
        _engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    logger.info(f"Set up session factory for database: {db_name}")


async def setup_connections(db_name: str = get_current_db()) -> None:
    """Set up both engine and session factory for the specified database"""
    await setup_engine(db_name)
    await setup_session_factory(db_name)
    set_current_db(db_name)
    logger.info(f"Set up connections for database: {db_name}")


async def get_engine() -> create_async_engine:
    """Get or create the SQLAlchemy engine"""
    global _engine
    if _engine is None:
        await setup_engine()
    return _engine


async def get_session_factory() -> async_sessionmaker:
    """Get or create the session factory"""
    global _session_factory
    if _session_factory is None:
        await setup_session_factory()
    return _session_factory


@asynccontextmanager
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get a database session as an async context manager"""
    logger.info(f"Getting database session for: {get_current_db()}")
    if _session_factory is None:
        await setup_session_factory()
    async with _session_factory() as session:
        try:
            yield session
        finally:
            await session.close()
            logger.info("Database session closed")


async def create_tables(engine) -> None:
    """Create all tables in the database"""
    logger.info("Creating database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Tables created successfully")


async def init_db(db_name: str = get_current_db()) -> None:
    """Initialize a new database with all required tables"""
    logger.info(f"Initializing database {db_name}")

    db_path = get_db_path(db_name)
    if not os.path.exists(db_path):
        logger.info(f"Creating new database file: {db_path}")
        with open(db_path, "w") as f:
            pass

    await setup_connections(db_name)
    set_current_db(db_name)

    await create_tables(await get_engine())

    available_dbs = get_available_databases()
    if db_name not in available_dbs:
        available_dbs.append(db_name)
        set_available_databases(available_dbs)

    logger.info(f"Initialized new database: {db_name}")


async def close_connections() -> None:
    """Close all database connections"""
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
        _engine = None
    _session_factory = None
    logger.info("Closed all database connections")


def generate_new_db_name() -> str:
    """Generate a new database name based on timestamp"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"db_{timestamp}"


def handle_uploaded_db(file_path: str) -> str:
    new_db_name = generate_new_db_name()
    new_db_path = get_db_path(new_db_name)
    shutil.copy2(file_path, new_db_path)
    return new_db_name
