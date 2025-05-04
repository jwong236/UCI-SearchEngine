"""
Database connection management
"""

import logging
import os
import shutil
from sqlalchemy import create_engine
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
_engine: Optional[create_engine] = None
_session_factory: Optional[async_sessionmaker] = None


def get_db_path(db_name: str = settings.DEFAULT_DB_NAME) -> str:
    """Get the full path to a database file"""
    # Ensure the data directory exists
    os.makedirs(settings.DB_DIR, exist_ok=True)
    return os.path.join(settings.DB_DIR, f"{db_name}.sqlite")


def get_db_url(db_name: str = settings.DEFAULT_DB_NAME) -> str:
    return f"sqlite+aiosqlite:///{get_db_path(db_name)}"


def setup_connections(db_name: str = get_current_db()) -> None:
    """Set up database connections for the specified database"""
    global _engine, _session_factory
    # Set the current database name
    set_current_db(db_name)
    setup_engine(db_name)
    setup_session_factory(db_name)

    # Add to available databases if not already present
    available_dbs = get_available_databases()
    if db_name not in available_dbs:
        available_dbs.append(db_name)
        set_available_databases(available_dbs)


def setup_engine(db_name: str = get_current_db()) -> None:
    """Set up the SQLAlchemy engine for the specified database"""
    global _engine
    if _engine is not None:
        _engine.dispose()

    # Ensure the database directory exists
    os.makedirs(settings.DB_DIR, exist_ok=True)

    # Create the database URL with the full path
    db_path = get_db_path(db_name)
    db_url = f"sqlite+aiosqlite:///{db_path}"

    _engine = create_async_engine(db_url)
    logger.info(f"Set up engine for database: {db_name}")


def setup_session_factory(db_name: str = get_current_db()) -> None:
    """Set up the SQLAlchemy session factory"""
    global _session_factory, _engine
    _session_factory = async_sessionmaker(
        autocommit=False, autoflush=False, bind=_engine
    )
    logger.info(f"Set up session factory for database: {db_name}")


def get_engine() -> create_engine:
    """
    Get or create the SQLAlchemy engine for the specified database
    """
    global _engine
    if _engine is None:
        logger.info("Creating new engine")
        setup_engine()
    return _engine


def get_session_factory() -> async_sessionmaker:
    """
    Get or create the session factory
    """
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            autocommit=False, autoflush=False, bind=get_engine()
        )
    return _session_factory


@asynccontextmanager
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Get a database session as an async context manager
    """
    logger.info(f"Getting database session for: {get_current_db()}")
    session_factory = get_session_factory()
    engine = get_engine()
    session_factory.configure(bind=engine)
    async with session_factory() as db:
        try:
            yield db
        finally:
            await db.close()
            logger.info("Database session closed")


async def create_tables(engine) -> None:
    """Create all tables in the database"""
    logger.info("Creating database tables...")
    logger.info(f"Tables in metadata: {Base.metadata.tables.keys()}")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Tables created successfully")


async def init_db(db_name: str = get_current_db()) -> None:
    """Initialize a new database with all required tables"""
    logger.info(f"Initializing database {db_name}")

    # Create the database file if it doesn't exist
    db_path = get_db_path(db_name)
    if not os.path.exists(db_path):
        logger.info(f"Creating new database file: {db_path}")
        # Create an empty file
        with open(db_path, "w") as f:
            pass

    # Set up connections to the new database
    setup_connections(db_name)

    # Create all tables
    await create_tables(get_engine())

    # Add to available databases if not already present
    available_dbs = get_available_databases()
    if db_name not in available_dbs:
        available_dbs.append(db_name)
        set_available_databases(available_dbs)

    logger.info(f"Initialized new database: {db_name}")


def close_connections() -> None:
    close_sessions()
    close_session_factory()
    close_engine()


def close_sessions() -> None:
    logger.info("Closing all sessions")
    # Sessions are closed when they go out of scope or explicitly closed


def close_session_factory() -> None:
    global _session_factory
    logger.info("Closing session factory")
    _session_factory = None


async def close_engine() -> None:
    global _engine
    logger.info("Closing engine")
    if _engine is not None:
        await _engine.dispose()
        _engine = None


def generate_new_db_name() -> str:
    """Generate a new database name based on timestamp"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"db_{timestamp}"


def handle_uploaded_db(file_path: str) -> str:
    new_db_name = generate_new_db_name()
    new_db_path = get_db_path(new_db_name)
    shutil.copy2(file_path, new_db_path)
    return new_db_name
