"""
Main application module
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.routes import router
from .config.globals import logger, get_available_databases, set_available_databases
from .database.connection import (
    get_db_path,
    init_db,
    setup_connections,
    close_connections,
)
from .config.settings import settings
import os


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    logger.info("Starting up application...")

    # Ensure data directory exists
    if not os.path.exists(settings.DB_DIR):
        logger.info(f"Creating data directory at {settings.DB_DIR}")
        os.makedirs(settings.DB_DIR, exist_ok=True)

    # Check if default database exists
    db_path = get_db_path(settings.DEFAULT_DB_NAME)
    if not os.path.exists(db_path):
        logger.info(
            f"Default database not found at {db_path}, initializing new database..."
        )
        # Initialize new database with tables
        init_db(settings.DEFAULT_DB_NAME)
    else:
        logger.info(f"Using existing database at {db_path}")
        # Set up connections to existing database
        setup_connections(settings.DEFAULT_DB_NAME)

    # Add default database to available databases if not already present
    available_dbs = get_available_databases()
    if settings.DEFAULT_DB_NAME not in available_dbs:
        available_dbs.append(settings.DEFAULT_DB_NAME)
        set_available_databases(available_dbs)

    yield

    # Shutdown
    logger.info("Shutting down application...")
    close_connections()


app = FastAPI(
    title="UCI Search Engine",
    description="A search engine for UCI websites",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "ws://localhost:3000",
        "ws://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api")
