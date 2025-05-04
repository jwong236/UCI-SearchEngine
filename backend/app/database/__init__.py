"""
Database package initialization.
This file makes the database directory a Python package and controls what is exposed when importing from it.
"""

# Import everything we want to expose from our modules
from .connection import (
    get_db,  # Get a database session
    get_engine,  # Get the database engine
    get_session_factory,  # Get the session factory
    init_db,  # Initialize a new database
    close_connections,  # Close all database connections
    get_db_path,
    setup_connections,
    generate_new_db_name,
    handle_uploaded_db,
)
from ..config.globals import (
    get_current_db,  # Get current database name
    set_current_db,  # Set current database name
    get_available_databases,  # Get list of available databases
)
from ..config.settings import settings
from .models import *

# List of what should be available when someone does:
# from app.database import *
__all__ = [
    # Connection functions
    "get_db",
    "get_engine",
    "get_session_factory",
    "init_db",
    "close_connections",
    "setup_connections",
    "generate_new_db_name",
    "handle_uploaded_db",
    # Configuration
    "get_current_db",
    "set_current_db",
    "get_available_databases",
    "get_db_path",
]
