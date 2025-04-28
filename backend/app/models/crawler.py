from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from ..database import Base


class URL(Base):
    __tablename__ = "urls"

    id = Column(Integer, primary_key=True)
    url = Column(String, unique=True)
    domain = Column(String)
    is_completed = Column(Boolean, default=False)
    status_code = Column(Integer)
    last_crawled = Column(DateTime)
    discovered_at = Column(DateTime, default=datetime.utcnow)
    word_count = Column(Integer)
    title = Column(String)
    content = Column(String)

    # Relationships
    outgoing_links = relationship(
        "URLRelationship",
        back_populates="source_url",
        foreign_keys="URLRelationship.source_url_id",
    )
    incoming_links = relationship(
        "URLRelationship",
        back_populates="target_url",
        foreign_keys="URLRelationship.target_url_id",
    )


class URLRelationship(Base):
    __tablename__ = "url_relationships"

    id = Column(Integer, primary_key=True)
    source_url_id = Column(Integer, ForeignKey("urls.id"))
    target_url_id = Column(Integer, ForeignKey("urls.id"))
    discovered_at = Column(DateTime, default=datetime.utcnow)

    source_url = relationship(
        "URL", back_populates="outgoing_links", foreign_keys=[source_url_id]
    )
    target_url = relationship(
        "URL", back_populates="incoming_links", foreign_keys=[target_url_id]
    )


class CrawlStatistics(Base):
    __tablename__ = "crawl_statistics"

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    urls_crawled = Column(Integer, default=0)
    urls_failed = Column(Integer, default=0)
    total_words = Column(Integer, default=0)
    unique_domains = Column(Integer, default=0)


class DomainRateLimit(Base):
    __tablename__ = "domain_rate_limits"

    id = Column(Integer, primary_key=True)
    domain = Column(String, unique=True)
    last_request = Column(DateTime)
    delay_seconds = Column(Float, default=1.0)
