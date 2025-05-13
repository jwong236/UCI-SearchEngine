"""
Main application module
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.routes import router
from .config.globals import (
    logger,
    get_available_databases,
    set_available_databases,
    set_current_db,
)
from .database.connection import (
    get_db_path,
    init_db,
    setup_connections,
    close_connections,
)
from .config.settings import settings
import os
import logging
from sqlalchemy import event
from sqlalchemy.engine import Engine

logging.getLogger("sqlalchemy").setLevel(logging.CRITICAL)
logging.getLogger("sqlalchemy.engine").setLevel(logging.CRITICAL)
logging.getLogger("sqlalchemy.pool").setLevel(logging.CRITICAL)
logging.getLogger("sqlalchemy.dialects").setLevel(logging.CRITICAL)
logging.getLogger("sqlalchemy.orm").setLevel(logging.CRITICAL)


@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan"""
    logger.info("Starting up application...")

    logging.getLogger("sqlalchemy").setLevel(logging.CRITICAL)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.CRITICAL)
    logging.getLogger("sqlalchemy.pool").setLevel(logging.CRITICAL)
    logging.getLogger("sqlalchemy.dialects").setLevel(logging.CRITICAL)
    logging.getLogger("sqlalchemy.orm").setLevel(logging.CRITICAL)

    os.makedirs(settings.DB_DIR, exist_ok=True)

    default_db_path = os.path.join(
        settings.DB_DIR, f"{settings.DEFAULT_DB_NAME}.sqlite"
    )
    if not os.path.exists(default_db_path):
        logger.info("Initializing new default database...")
        await init_db(settings.DEFAULT_DB_NAME)
    else:
        logger.info(f"Using existing database at {default_db_path}")
        await setup_connections(settings.DEFAULT_DB_NAME)

    set_current_db(settings.DEFAULT_DB_NAME)

    available_dbs = get_available_databases()
    if settings.DEFAULT_DB_NAME not in available_dbs:
        available_dbs.append(settings.DEFAULT_DB_NAME)
        set_available_databases(available_dbs)
        logger.info(f"Available databases updated: {available_dbs}")

    logger.info("Application startup complete.")
    yield
    logger.info("Shutting down application...")
    await close_connections()
    logger.info("Application shutdown complete.")


app = FastAPI(
    title="UCI Search Engine",
    description="A search engine for UCI websites",
    version="1.0.0",
    lifespan=lifespan,
)

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

app.include_router(router, prefix="/api")
