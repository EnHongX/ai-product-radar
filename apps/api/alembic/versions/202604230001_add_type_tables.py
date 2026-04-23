"""Add company_types and source_types tables.

Revision ID: 202604230001
Revises: 202604220002
Create Date: 2026-04-23
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from slugify import slugify

revision: str = "202604230001"
down_revision: str = "202604220002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def timestamps() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "company_types",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("enabled", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        *timestamps(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_company_types_name"),
        sa.UniqueConstraint("slug", name="uq_company_types_slug"),
    )
    op.create_index("ix_company_types_enabled", "company_types", ["enabled"])

    op.create_table(
        "source_types",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("enabled", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        *timestamps(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_source_types_name"),
        sa.UniqueConstraint("slug", name="uq_source_types_slug"),
    )
    op.create_index("ix_source_types_enabled", "source_types", ["enabled"])

    company_types_table = sa.table(
        "company_types",
        sa.column("id", sa.BigInteger),
        sa.column("name", sa.String),
        sa.column("slug", sa.String),
        sa.column("enabled", sa.Boolean),
    )

    default_company_types = [
        {"name": "科技公司", "slug": "tech-company", "enabled": True},
        {"name": "初创企业", "slug": "startup", "enabled": True},
        {"name": "大型企业", "slug": "enterprise", "enabled": True},
        {"name": "研究机构", "slug": "research-institute", "enabled": True},
        {"name": "大学", "slug": "university", "enabled": True},
        {"name": "其他", "slug": "other", "enabled": True},
    ]

    op.bulk_insert(company_types_table, default_company_types)

    source_types_table = sa.table(
        "source_types",
        sa.column("id", sa.BigInteger),
        sa.column("name", sa.String),
        sa.column("slug", sa.String),
        sa.column("enabled", sa.Boolean),
    )

    default_source_types = [
        {"name": "博客", "slug": "blog", "enabled": True},
        {"name": "RSS订阅", "slug": "rss", "enabled": True},
        {"name": "新闻通讯", "slug": "newsletter", "enabled": True},
        {"name": "社交媒体", "slug": "social", "enabled": True},
        {"name": "文档", "slug": "documentation", "enabled": True},
        {"name": "变更日志", "slug": "changelog", "enabled": True},
        {"name": "其他", "slug": "other", "enabled": True},
    ]

    op.bulk_insert(source_types_table, default_source_types)


def downgrade() -> None:
    op.drop_index("ix_source_types_enabled", table_name="source_types")
    op.drop_table("source_types")
    op.drop_index("ix_company_types_enabled", table_name="company_types")
    op.drop_table("company_types")
