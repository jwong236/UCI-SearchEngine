from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
import os

# Create database directory if it doesn't exist
os.makedirs("backend/app/database", exist_ok=True)

# Create database engine
engine = create_engine("sqlite:///backend/app/database/crawler.db")


# Create base class for models
class Base(DeclarativeBase):
    pass


# Create session factory
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


# Function to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database with required tables."""
    from .models.crawler import URL, URLRelationship, DomainRateLimit, CrawlStatistics

    Base.metadata.create_all(bind=engine)
