from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class Company(TimestampMixin, Base):
    __tablename__ = "companies"
    __table_args__ = (
        UniqueConstraint("name", name="uq_companies_name"),
        UniqueConstraint("slug", name="uq_companies_slug"),
        Index("ix_companies_company_type", "company_type"),
        Index("ix_companies_slug", "slug"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False)
    website: Mapped[str | None] = mapped_column(String(2048))
    country: Mapped[str | None] = mapped_column(String(80))
    company_type: Mapped[str] = mapped_column(String(64), nullable=False)
    logo_url: Mapped[str | None] = mapped_column(String(2048))
    description: Mapped[str | None] = mapped_column(Text)

    sources: Mapped[list["Source"]] = relationship(back_populates="company", cascade="all, delete-orphan")
    products: Mapped[list["Product"]] = relationship(back_populates="company", cascade="all, delete-orphan")


class Source(TimestampMixin, Base):
    __tablename__ = "sources"
    __table_args__ = (
        UniqueConstraint("url", name="uq_sources_url"),
        Index("ix_sources_company_id", "company_id"),
        Index("ix_sources_enabled", "enabled"),
        Index("ix_sources_source_type", "source_type"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    source_type: Mapped[str] = mapped_column(String(64), nullable=False)
    parse_strategy: Mapped[str] = mapped_column(String(64), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, server_default="true", nullable=False)
    crawl_interval_hours: Mapped[int] = mapped_column(Integer, server_default="24", nullable=False)
    last_crawled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    company: Mapped[Company] = relationship(back_populates="sources")
    raw_articles: Mapped[list["RawArticle"]] = relationship(back_populates="source", cascade="all, delete-orphan")
    product_releases: Mapped[list["ProductRelease"]] = relationship(back_populates="source")
    crawl_logs: Mapped[list["CrawlLog"]] = relationship(back_populates="source", cascade="all, delete-orphan")


class Platform(TimestampMixin, Base):
    __tablename__ = "platforms"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)

    release_links: Mapped[list["ReleasePlatform"]] = relationship(back_populates="platform", cascade="all, delete-orphan")


class Product(TimestampMixin, Base):
    __tablename__ = "products"
    __table_args__ = (
        UniqueConstraint("company_id", "slug", name="uq_products_company_slug"),
        UniqueConstraint("official_url", name="uq_products_official_url"),
        Index("ix_products_category", "category"),
        Index("ix_products_company_id", "company_id"),
        Index("ix_products_status", "status"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False)
    official_url: Mapped[str | None] = mapped_column(String(2048))
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    pricing_model: Mapped[str | None] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(64), server_default="active", nullable=False)

    company: Mapped[Company] = relationship(back_populates="products")
    releases: Mapped[list["ProductRelease"]] = relationship(back_populates="product")


class RawArticle(TimestampMixin, Base):
    __tablename__ = "raw_articles"
    __table_args__ = (
        UniqueConstraint("content_hash", name="uq_raw_articles_content_hash"),
        UniqueConstraint("url", name="uq_raw_articles_url"),
        Index("ix_raw_articles_published_at", "published_at"),
        Index("ix_raw_articles_source_id", "source_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    author: Mapped[str | None] = mapped_column(String(255))
    content: Mapped[str | None] = mapped_column(Text)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    raw_metadata: Mapped[dict | None] = mapped_column(JSONB)

    source: Mapped[Source] = relationship(back_populates="raw_articles")
    product_releases: Mapped[list["ProductRelease"]] = relationship(back_populates="raw_article")
    review_tasks: Mapped[list["ReviewTask"]] = relationship(back_populates="raw_article")
    extraction_logs: Mapped[list["ExtractionLog"]] = relationship(back_populates="raw_article")


class ProductRelease(TimestampMixin, Base):
    __tablename__ = "product_releases"
    __table_args__ = (
        UniqueConstraint("raw_content_hash", name="uq_product_releases_raw_content_hash"),
        UniqueConstraint("release_url", name="uq_product_releases_release_url"),
        Index("ix_product_releases_product_id", "product_id"),
        Index("ix_product_releases_release_date", "release_date"),
        Index("ix_product_releases_release_type", "release_type"),
        Index("ix_product_releases_review_status", "review_status"),
        Index("ix_product_releases_source_id", "source_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id", ondelete="SET NULL"))
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id", ondelete="CASCADE"), nullable=False)
    raw_article_id: Mapped[int | None] = mapped_column(ForeignKey("raw_articles.id", ondelete="SET NULL"))
    release_title: Mapped[str] = mapped_column(String(512), nullable=False)
    release_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    release_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    release_type: Mapped[str] = mapped_column(String(64), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text)
    confidence_score: Mapped[float | None] = mapped_column(Float)
    review_status: Mapped[str] = mapped_column(String(64), server_default="pending", nullable=False)
    raw_content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    extraction_payload: Mapped[dict | None] = mapped_column(JSONB)

    product: Mapped[Product | None] = relationship(back_populates="releases")
    source: Mapped[Source] = relationship(back_populates="product_releases")
    raw_article: Mapped[RawArticle | None] = relationship(back_populates="product_releases")
    platform_links: Mapped[list["ReleasePlatform"]] = relationship(back_populates="release", cascade="all, delete-orphan")
    review_tasks: Mapped[list["ReviewTask"]] = relationship(back_populates="product_release")
    extraction_logs: Mapped[list["ExtractionLog"]] = relationship(back_populates="product_release")


class ReleasePlatform(Base):
    __tablename__ = "release_platforms"
    __table_args__ = (Index("ix_release_platforms_platform_id", "platform_id"),)

    release_id: Mapped[int] = mapped_column(ForeignKey("product_releases.id", ondelete="CASCADE"), primary_key=True)
    platform_id: Mapped[int] = mapped_column(ForeignKey("platforms.id", ondelete="CASCADE"), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    release: Mapped[ProductRelease] = relationship(back_populates="platform_links")
    platform: Mapped[Platform] = relationship(back_populates="release_links")


class ReviewTask(TimestampMixin, Base):
    __tablename__ = "review_tasks"
    __table_args__ = (
        Index("ix_review_tasks_priority", "priority"),
        Index("ix_review_tasks_status", "status"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    raw_article_id: Mapped[int | None] = mapped_column(ForeignKey("raw_articles.id", ondelete="SET NULL"))
    product_release_id: Mapped[int | None] = mapped_column(ForeignKey("product_releases.id", ondelete="SET NULL"))
    status: Mapped[str] = mapped_column(String(64), server_default="pending", nullable=False)
    priority: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)
    assigned_to: Mapped[str | None] = mapped_column(String(255))
    reviewer_notes: Mapped[str | None] = mapped_column(Text)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    raw_article: Mapped[RawArticle | None] = relationship(back_populates="review_tasks")
    product_release: Mapped[ProductRelease | None] = relationship(back_populates="review_tasks")


class CrawlLog(Base):
    __tablename__ = "crawl_logs"
    __table_args__ = (
        Index("ix_crawl_logs_source_id", "source_id"),
        Index("ix_crawl_logs_started_at", "started_at"),
        Index("ix_crawl_logs_status", "status"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id", ondelete="CASCADE"), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(64), nullable=False)
    articles_found: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)
    articles_created: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text)
    log_metadata: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    source: Mapped[Source] = relationship(back_populates="crawl_logs")


class ExtractionLog(Base):
    __tablename__ = "extraction_logs"
    __table_args__ = (
        Index("ix_extraction_logs_created_at", "created_at"),
        Index("ix_extraction_logs_raw_article_id", "raw_article_id"),
        Index("ix_extraction_logs_status", "status"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    raw_article_id: Mapped[int] = mapped_column(ForeignKey("raw_articles.id", ondelete="CASCADE"), nullable=False)
    product_release_id: Mapped[int | None] = mapped_column(ForeignKey("product_releases.id", ondelete="SET NULL"))
    status: Mapped[str] = mapped_column(String(64), nullable=False)
    model_name: Mapped[str | None] = mapped_column(String(120))
    prompt_version: Mapped[str | None] = mapped_column(String(64))
    input_hash: Mapped[str | None] = mapped_column(String(64))
    output_payload: Mapped[dict | None] = mapped_column(JSONB)
    error_message: Mapped[str | None] = mapped_column(Text)
    confidence_score: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    raw_article: Mapped[RawArticle] = relationship(back_populates="extraction_logs")
    product_release: Mapped[ProductRelease | None] = relationship(back_populates="extraction_logs")
