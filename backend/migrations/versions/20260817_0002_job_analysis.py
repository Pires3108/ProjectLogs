"""Persist structured job analysis.

Revision ID: 20260817_0002
Revises: 20260817_0001
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260817_0002"
down_revision: str | None = "20260817_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("jobs", sa.Column("analysis_data", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("jobs", "analysis_data")
