"""create endpoints and subscriptions

Revision ID: cf517433ae2b
Revises: dc6ef21a00ef
Create Date: 2026-10-23 13:47:24.397586

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "cf517433ae2b"
down_revision: str | Sequence[str] | None = "dc6ef21a00ef"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Standard Webhooks event type: dot-delimited, [a-zA-Z0-9_],
# e.g. invoice.paid, user.profile.updated.
EVENT_TYPE_PATTERN = r"^[a-zA-Z0-9_]+(\.[a-zA-Z0-9_]+)*$"


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "endpoints",
        sa.Column("id", sa.Uuid, server_default=sa.text("uuidv7()"), nullable=False),
        sa.Column("tenant_id", sa.Uuid, nullable=False),
        sa.Column("url", sa.Text, nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("status", sa.Text, server_default="active", nullable=False),
        sa.Column("disabled_reason", sa.Text),
        sa.Column("disabled_at", sa.DateTime(timezone=True)),
        sa.Column("secret_ciphertext", postgresql.BYTEA, nullable=False),
        sa.Column("previous_secret_ciphertext", postgresql.BYTEA),
        sa.Column("previous_secret_expires_at", sa.DateTime(timezone=True)),
        # Which KEK encrypted the secrets.
        sa.Column("secret_key_version", sa.SmallInteger, nullable=False),
        sa.Column(
            "max_concurrency",
            sa.SmallInteger,
            server_default=sa.text("10"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="endpoints_pkey"),
        sa.ForeignKeyConstraint(
            ["tenant_id"], ["tenants.id"], name="endpoints_tenant_id_fkey"
        ),
        # Target of the composite (id, tenant_id) FKs.
        sa.UniqueConstraint("id", "tenant_id", name="endpoints_id_tenant_id_key"),
        sa.CheckConstraint(
            "status IN ('active', 'disabled', 'deleted')",
            name="endpoints_status_check",
        ),
        sa.CheckConstraint(
            "disabled_reason IN ('manual', 'gone_410', 'failing', 'operator')",
            name="endpoints_disabled_reason_check",
        ),
        sa.CheckConstraint(
            "max_concurrency BETWEEN 1 AND 100",
            name="endpoints_max_concurrency_check",
        ),
        sa.CheckConstraint(
            "(status = 'disabled') = (disabled_reason IS NOT NULL)",
            name="endpoints_check",
        ),
        sa.CheckConstraint(
            "(previous_secret_ciphertext IS NULL)"
            " = (previous_secret_expires_at IS NULL)",
            name="endpoints_check1",
        ),
    )
    op.create_index(
        "endpoints_tenant_idx",
        "endpoints",
        ["tenant_id"],
        postgresql_where=sa.text("status <> 'deleted'"),
    )

    op.create_table(
        "subscriptions",
        sa.Column("id", sa.Uuid, server_default=sa.text("uuidv7()"), nullable=False),
        sa.Column("tenant_id", sa.Uuid, nullable=False),
        sa.Column("endpoint_id", sa.Uuid, nullable=False),
        sa.Column("event_type", sa.Text, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="subscriptions_pkey"),
        sa.UniqueConstraint(
            "endpoint_id",
            "event_type",
            name="subscriptions_endpoint_id_event_type_key",
        ),
        sa.ForeignKeyConstraint(
            ["endpoint_id", "tenant_id"],
            ["endpoints.id", "endpoints.tenant_id"],
            name="subscriptions_endpoint_id_tenant_id_fkey",
            ondelete="CASCADE",
        ),
        sa.CheckConstraint(
            f"event_type = '*' OR event_type ~ '{EVENT_TYPE_PATTERN}'",
            name="subscriptions_event_type_check",
        ),
    )
    op.create_index(
        "subscriptions_fanout_idx", "subscriptions", ["tenant_id", "event_type"]
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("subscriptions_fanout_idx", table_name="subscriptions")
    op.drop_table("subscriptions")
    op.drop_index("endpoints_tenant_idx", table_name="endpoints")
    op.drop_table("endpoints")
