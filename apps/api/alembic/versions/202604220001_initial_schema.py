"""Initial schema for AI Product Radar.

Revision ID: 202604220001
Revises:
Create Date: 2026-04-22
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "202604220001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def timestamps() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    ]


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "companies",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("website", sa.String(length=2048), nullable=True),
        sa.Column("country", sa.String(length=80), nullable=True),
        sa.Column("company_type", sa.String(length=64), nullable=False),
        sa.Column("logo_url", sa.String(length=2048), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        *timestamps(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_companies_name"),
        sa.UniqueConstraint("slug", name="uq_companies_slug"),
    )
    op.create_index("ix_companies_company_type", "companies", ["company_type"])
    op.create_index("ix_companies_slug", "companies", ["slug"])

    op.create_table(
        "sources",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("company_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("url", sa.String(length=2048), nullable=False),
        sa.Column("source_type", sa.String(length=64), nullable=False),
        sa.Column("parse_strategy", sa.String(length=64), nullable=False),
        sa.Column("enabled", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("crawl_interval_hours", sa.Integer(), server_default="24", nullable=False),
        sa.Column("last_crawled_at", sa.DateTime(timezone=True), nullable=True),
        *timestamps(),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("url", name="uq_sources_url"),
    )
    op.create_index("ix_sources_company_id", "sources", ["company_id"])
    op.create_index("ix_sources_enabled", "sources", ["enabled"])
    op.create_index("ix_sources_source_type", "sources", ["source_type"])

    op.create_table(
        "platforms",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        *timestamps(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_platforms_name"),
        sa.UniqueConstraint("slug", name="uq_platforms_slug"),
    )

    op.create_table(
        "products",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("company_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("official_url", sa.String(length=2048), nullable=True),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("pricing_model", sa.String(length=64), nullable=True),
        sa.Column("status", sa.String(length=64), server_default="active", nullable=False),
        *timestamps(),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("company_id", "slug", name="uq_products_company_slug"),
        sa.UniqueConstraint("official_url", name="uq_products_official_url"),
    )
    op.create_index("ix_products_category", "products", ["category"])
    op.create_index("ix_products_company_id", "products", ["company_id"])
    op.create_index("ix_products_status", "products", ["status"])

    op.create_table(
        "raw_articles",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("source_id", sa.BigInteger(), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("url", sa.String(length=2048), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("author", sa.String(length=255), nullable=True),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("raw_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        *timestamps(),
        sa.ForeignKeyConstraint(["source_id"], ["sources.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("content_hash", name="uq_raw_articles_content_hash"),
        sa.UniqueConstraint("url", name="uq_raw_articles_url"),
    )
    op.create_index("ix_raw_articles_published_at", "raw_articles", ["published_at"])
    op.create_index("ix_raw_articles_source_id", "raw_articles", ["source_id"])

    op.create_table(
        "product_releases",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("product_id", sa.BigInteger(), nullable=True),
        sa.Column("source_id", sa.BigInteger(), nullable=False),
        sa.Column("raw_article_id", sa.BigInteger(), nullable=True),
        sa.Column("release_title", sa.String(length=512), nullable=False),
        sa.Column("release_url", sa.String(length=2048), nullable=False),
        sa.Column("release_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("release_type", sa.String(length=64), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column("review_status", sa.String(length=64), server_default="pending", nullable=False),
        sa.Column("raw_content_hash", sa.String(length=64), nullable=False),
        sa.Column("extraction_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        *timestamps(),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["raw_article_id"], ["raw_articles.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["source_id"], ["sources.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("raw_content_hash", name="uq_product_releases_raw_content_hash"),
        sa.UniqueConstraint("release_url", name="uq_product_releases_release_url"),
    )
    op.create_index("ix_product_releases_product_id", "product_releases", ["product_id"])
    op.create_index("ix_product_releases_release_date", "product_releases", ["release_date"])
    op.create_index("ix_product_releases_release_type", "product_releases", ["release_type"])
    op.create_index("ix_product_releases_review_status", "product_releases", ["review_status"])
    op.create_index("ix_product_releases_source_id", "product_releases", ["source_id"])

    op.create_table(
        "release_platforms",
        sa.Column("release_id", sa.BigInteger(), nullable=False),
        sa.Column("platform_id", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["platform_id"], ["platforms.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["release_id"], ["product_releases.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("release_id", "platform_id"),
    )
    op.create_index("ix_release_platforms_platform_id", "release_platforms", ["platform_id"])

    op.create_table(
        "review_tasks",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("raw_article_id", sa.BigInteger(), nullable=True),
        sa.Column("product_release_id", sa.BigInteger(), nullable=True),
        sa.Column("status", sa.String(length=64), server_default="pending", nullable=False),
        sa.Column("priority", sa.Integer(), server_default="0", nullable=False),
        sa.Column("assigned_to", sa.String(length=255), nullable=True),
        sa.Column("reviewer_notes", sa.Text(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        *timestamps(),
        sa.ForeignKeyConstraint(["product_release_id"], ["product_releases.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["raw_article_id"], ["raw_articles.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_review_tasks_priority", "review_tasks", ["priority"])
    op.create_index("ix_review_tasks_status", "review_tasks", ["status"])

    op.create_table(
        "crawl_logs",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("source_id", sa.BigInteger(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("articles_found", sa.Integer(), server_default="0", nullable=False),
        sa.Column("articles_created", sa.Integer(), server_default="0", nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("log_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["source_id"], ["sources.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_crawl_logs_source_id", "crawl_logs", ["source_id"])
    op.create_index("ix_crawl_logs_started_at", "crawl_logs", ["started_at"])
    op.create_index("ix_crawl_logs_status", "crawl_logs", ["status"])

    op.create_table(
        "extraction_logs",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("raw_article_id", sa.BigInteger(), nullable=False),
        sa.Column("product_release_id", sa.BigInteger(), nullable=True),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("model_name", sa.String(length=120), nullable=True),
        sa.Column("prompt_version", sa.String(length=64), nullable=True),
        sa.Column("input_hash", sa.String(length=64), nullable=True),
        sa.Column("output_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["product_release_id"], ["product_releases.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["raw_article_id"], ["raw_articles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_extraction_logs_created_at", "extraction_logs", ["created_at"])
    op.create_index("ix_extraction_logs_raw_article_id", "extraction_logs", ["raw_article_id"])
    op.create_index("ix_extraction_logs_status", "extraction_logs", ["status"])


def downgrade() -> None:
    op.drop_index("ix_extraction_logs_status", table_name="extraction_logs")
    op.drop_index("ix_extraction_logs_raw_article_id", table_name="extraction_logs")
    op.drop_index("ix_extraction_logs_created_at", table_name="extraction_logs")
    op.drop_table("extraction_logs")

    op.drop_index("ix_crawl_logs_status", table_name="crawl_logs")
    op.drop_index("ix_crawl_logs_started_at", table_name="crawl_logs")
    op.drop_index("ix_crawl_logs_source_id", table_name="crawl_logs")
    op.drop_table("crawl_logs")

    op.drop_index("ix_review_tasks_status", table_name="review_tasks")
    op.drop_index("ix_review_tasks_priority", table_name="review_tasks")
    op.drop_table("review_tasks")

    op.drop_index("ix_release_platforms_platform_id", table_name="release_platforms")
    op.drop_table("release_platforms")

    op.drop_index("ix_product_releases_source_id", table_name="product_releases")
    op.drop_index("ix_product_releases_review_status", table_name="product_releases")
    op.drop_index("ix_product_releases_release_type", table_name="product_releases")
    op.drop_index("ix_product_releases_release_date", table_name="product_releases")
    op.drop_index("ix_product_releases_product_id", table_name="product_releases")
    op.drop_table("product_releases")

    op.drop_index("ix_raw_articles_source_id", table_name="raw_articles")
    op.drop_index("ix_raw_articles_published_at", table_name="raw_articles")
    op.drop_table("raw_articles")

    op.drop_index("ix_products_status", table_name="products")
    op.drop_index("ix_products_company_id", table_name="products")
    op.drop_index("ix_products_category", table_name="products")
    op.drop_table("products")

    op.drop_table("platforms")

    op.drop_index("ix_sources_source_type", table_name="sources")
    op.drop_index("ix_sources_enabled", table_name="sources")
    op.drop_index("ix_sources_company_id", table_name="sources")
    op.drop_table("sources")

    op.drop_index("ix_companies_slug", table_name="companies")
    op.drop_index("ix_companies_company_type", table_name="companies")
    op.drop_table("companies")
