"""
Database package initialization.
This file makes the database directory a Python package and controls what is exposed when importing from it.
"""

from .connection import (
    get_db,
    get_engine,
    get_session_factory,
    init_db,
    close_connections,
    get_db_path,
    setup_connections,
    generate_new_db_name,
    handle_uploaded_db,
)
from ..config.globals import (
    get_current_db,
    set_current_db,
    get_available_databases,
)
from ..config.settings import settings
from .models import *

__all__ = [
    "get_db",
    "get_engine",
    "get_session_factory",
    "init_db",
    "close_connections",
    "setup_connections",
    "generate_new_db_name",
    "handle_uploaded_db",
    "get_current_db",
    "set_current_db",
    "get_available_databases",
    "get_db_path",
]
