"""Persist generated HTML for ephemeral free runtimes.

Revision ID: 20260817_0003
Revises: 20260817_0002
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260817_0003"
down_revision: str | None = "20260817_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("jobs", sa.Column("html_content", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("jobs", "html_content")
