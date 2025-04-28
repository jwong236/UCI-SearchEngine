from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# Create database engine
engine = create_engine("sqlite:///crawler.db")


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
