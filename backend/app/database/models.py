"""
Database models for the UCI Search Engine.
"""

from typing import List
from sqlalchemy import (
    ForeignKey,
    Column,
    Integer,
    String,
    DateTime,
    Float,
    Boolean,
    Text,
    Index,
)
from sqlalchemy.orm import relationship, Mapped, mapped_column, DeclarativeBase
from datetime import datetime, timezone


class Base(DeclarativeBase):
    pass


class Term(Base):
    """Model for storing terms from documents"""

    __tablename__ = "terms"

    id: Mapped[int] = mapped_column(primary_key=True)
    term: Mapped[str] = mapped_column(unique=True, index=True)
    document_frequency: Mapped[int] = mapped_column(default=0)

    document_terms: Mapped[List["DocumentTerm"]] = relationship(back_populates="term")
    stats: Mapped["TermStats"] = relationship(back_populates="term", uselist=False)
    inverted_index_entries: Mapped[List["InvertedIndex"]] = relationship(
        back_populates="term"
    )

    # Indexes
    __table_args__ = (Index("idx_terms_term", "term"),)


class TermStats(Base):
    __tablename__ = "term_stats"

    id: Mapped[int] = mapped_column(primary_key=True)
    term_id: Mapped[int] = mapped_column(ForeignKey("terms.id"), unique=True)
    document_frequency: Mapped[int] = mapped_column(default=0)

    term: Mapped["Term"] = relationship(back_populates="stats")


class DocumentTerm(Base):
    __tablename__ = "document_terms"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"))
    term_id: Mapped[int] = mapped_column(ForeignKey("terms.id"))
    normalized_frequency: Mapped[float] = mapped_column(default=0.0)

    document: Mapped["Document"] = relationship(back_populates="document_terms")
    term: Mapped["Term"] = relationship(back_populates="document_terms")


class Document(Base):
    """Model for storing crawled documents"""

    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    url: Mapped[str] = mapped_column(unique=True, index=True)
    title: Mapped[str] = mapped_column()
    content: Mapped[str] = mapped_column()
    discovered_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )
    last_crawled_at: Mapped[datetime | None] = mapped_column()
    is_crawled: Mapped[bool] = mapped_column(default=False)
    crawl_failed: Mapped[bool] = mapped_column(default=False)
    error_message: Mapped[str | None] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    document_terms: Mapped[List["DocumentTerm"]] = relationship(
        back_populates="document"
    )
    outgoing_links: Mapped[List["DocumentRelationship"]] = relationship(
        back_populates="source_document",
        foreign_keys="DocumentRelationship.source_document_id",
    )
    incoming_links: Mapped[List["DocumentRelationship"]] = relationship(
        back_populates="target_document",
        foreign_keys="DocumentRelationship.target_document_id",
    )
    inverted_index_entries: Mapped[List["InvertedIndex"]] = relationship(
        back_populates="document"
    )

    # Indexes
    __table_args__ = (
        Index("idx_documents_url", "url"),
        Index("idx_documents_is_crawled", "is_crawled"),
    )


class Statistics(Base):
    __tablename__ = "statistics"

    id: Mapped[int] = mapped_column(primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )
    documents_crawled: Mapped[int] = mapped_column(default=0)
    documents_failed: Mapped[int] = mapped_column(default=0)
    total_terms: Mapped[int] = mapped_column(default=0)


class DocumentRelationship(Base):
    __tablename__ = "document_relationships"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"))
    target_document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"))
    discovered_at: Mapped[datetime] = mapped_column(default=datetime.now(timezone.utc))

    source_document: Mapped["Document"] = relationship(
        back_populates="outgoing_links",
        foreign_keys=[source_document_id],
    )
    target_document: Mapped["Document"] = relationship(
        back_populates="incoming_links",
        foreign_keys=[target_document_id],
    )


class CrawlStatistics(Base):
    __tablename__ = "crawl_statistics"

    id: Mapped[int] = mapped_column(primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(default=datetime.now(timezone.utc))
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


class CrawlerState(Base):
    """Model for tracking crawler state"""

    __tablename__ = "crawler_state"

    id = Column(Integer, primary_key=True)
    current_url = Column(String)
    urls_visited = Column(Integer, default=0)
    urls_failed = Column(Integer, default=0)
    urls_queued = Column(Integer, default=0)
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class InvertedIndex(Base):
    """Model for storing the inverted index"""

    __tablename__ = "inverted_index"

    id: Mapped[int] = mapped_column(primary_key=True)
    term_id: Mapped[int] = mapped_column(ForeignKey("terms.id"))
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"))
    term_frequency: Mapped[int] = mapped_column()
    tf_idf: Mapped[float] = mapped_column()

    term: Mapped["Term"] = relationship(back_populates="inverted_index_entries")
    document: Mapped["Document"] = relationship(back_populates="inverted_index_entries")

    # Indexes
    __table_args__ = (Index("idx_inverted_index_term_doc", "term_id", "document_id"),)
