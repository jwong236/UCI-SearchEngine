from typing import List
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Float,
    LargeBinary,
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime
from ..database import Base


class URL(Base):
    __tablename__ = "urls"

    id: Mapped[int] = mapped_column(primary_key=True)
    url: Mapped[str] = mapped_column(unique=True)
    domain: Mapped[str] = mapped_column()
    is_completed: Mapped[bool] = mapped_column(default=False)
    status_code: Mapped[int | None] = mapped_column()
    last_crawled: Mapped[datetime | None] = mapped_column()
    discovered_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    word_count: Mapped[int | None] = mapped_column()

    # Search-relevant content
    title: Mapped[str | None] = mapped_column()
    text_content: Mapped[str | None] = mapped_column()  # Clean text without HTML
    document_vector: Mapped[bytes | None] = mapped_column(LargeBinary)  # TF-IDF vector
    meta_description: Mapped[str | None] = mapped_column()  # For search snippets
    important_headings: Mapped[str | None] = (
        mapped_column()
    )  # JSON string of important headings

    # Relationships
    outgoing_links: Mapped[List["URLRelationship"]] = relationship(
        back_populates="source_url",
        foreign_keys="URLRelationship.source_url_id",
    )
    incoming_links: Mapped[List["URLRelationship"]] = relationship(
        back_populates="target_url",
        foreign_keys="URLRelationship.target_url_id",
    )


class URLRelationship(Base):
    __tablename__ = "url_relationships"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_url_id: Mapped[int] = mapped_column(ForeignKey("urls.id"))
    target_url_id: Mapped[int] = mapped_column(ForeignKey("urls.id"))
    discovered_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    source_url: Mapped["URL"] = relationship(
        back_populates="outgoing_links",
        foreign_keys=[source_url_id],
    )
    target_url: Mapped["URL"] = relationship(
        back_populates="incoming_links",
        foreign_keys=[target_url_id],
    )


class CrawlStatistics(Base):
    __tablename__ = "crawl_statistics"

    id: Mapped[int] = mapped_column(primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    urls_crawled: Mapped[int] = mapped_column(default=0)
    urls_failed: Mapped[int] = mapped_column(default=0)
    total_words: Mapped[int] = mapped_column(default=0)
    unique_domains: Mapped[int] = mapped_column(default=0)


class DomainRateLimit(Base):
    __tablename__ = "domain_rate_limits"

    id: Mapped[int] = mapped_column(primary_key=True)
    domain: Mapped[str] = mapped_column(unique=True)
    last_request: Mapped[datetime | None] = mapped_column()
    delay_seconds: Mapped[float] = mapped_column(default=1.0)
