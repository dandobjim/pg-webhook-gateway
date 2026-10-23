"""create audit log

Revision ID: 97698e49f2d2
Revises: eb43f8e51ceb
Create Date: 2026-10-23 13:47:24.925141

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "97698e49f2d2"
down_revision: str | Sequence[str] | None = "eb43f8e51ceb"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "audit_log",
        sa.Column("id", sa.BigInteger, sa.Identity(always=True), nullable=False),
        sa.Column(
            "occurred_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("actor_type", sa.Text, nullable=False),
        sa.Column("actor_id", sa.Text, nullable=False),
        sa.Column("tenant_id", sa.Uuid),
        # e.g. delivery.replayed, endpoint.disabled.
        sa.Column("action", sa.Text, nullable=False),
        sa.Column("target_type", sa.Text, nullable=False),
        sa.Column("target_id", sa.Text, nullable=False),
        sa.Column("details", postgresql.JSONB, server_default="{}", nullable=False),
        sa.PrimaryKeyConstraint("id", name="audit_log_pkey"),
        sa.ForeignKeyConstraint(
            ["tenant_id"], ["tenants.id"], name="audit_log_tenant_id_fkey"
        ),
        sa.CheckConstraint(
            "actor_type IN ('operator', 'tenant', 'system')",
            name="audit_log_actor_type_check",
        ),
    )
    op.create_index(
        "audit_log_tenant_idx",
        "audit_log",
        ["tenant_id", sa.text("occurred_at DESC")],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("audit_log_tenant_idx", table_name="audit_log")
    op.drop_table("audit_log")
