"""Add finished_at column to extraction_logs table.

Revision ID: 202604260001
Revises: 202604230001
Create Date: 2026-04-26
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "202604260001"
down_revision: str = "202604230001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "extraction_logs",
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("extraction_logs", "finished_at")
