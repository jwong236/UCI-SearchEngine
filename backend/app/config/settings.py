"""
Application settings using Pydantic v2.
"""

from pydantic import BaseModel, Field
from typing import List
import os


class Settings(BaseModel):
    """Application settings"""

    # API settings
    API_HOST: str = Field(default="0.0.0.0")
    API_PORT: int = Field(default=8000)
    SECRET_KEY: str = Field(default="jacob-secret-key")

    # Database settings
    DEFAULT_DB_NAME: str = Field(default="db-default")
    DB_DIR: str = Field(
        default=os.path.join(
            os.path.dirname(os.path.dirname(__file__)),  # app directory
            "database",  # database directory
            "data",  # data directory
        )
    )
    DATABASE_URL: str = Field(default="sqlite:///database/data/db-default.sqlite")

    # Crawler settings
    CRAWLER_SEED_URLS: List[str] = Field(
        default=[
            "https://www.ics.uci.edu",
            "https://www.cs.uci.edu",
            "https://www.informatics.uci.edu",
            "https://www.stat.uci.edu",
        ]
    )
    CRAWLER_MAX_DEPTH: int = Field(default=3)
    CRAWLER_MAX_PAGES: int = Field(default=100)
    CRAWLER_DELAY: float = Field(default=1.0)


# Create settings instance
settings = Settings()
