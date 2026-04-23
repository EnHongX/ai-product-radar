"""Empty migration to match database version.

Revision ID: 202604220002
Revises: 202604220001
Create Date: 2026-04-22
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "202604220002"
down_revision: str | None = "202604220001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
