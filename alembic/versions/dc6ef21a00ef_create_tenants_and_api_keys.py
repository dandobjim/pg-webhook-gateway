"""create tenants and api keys

Revision ID: dc6ef21a00ef
Revises:
Create Date: 2026-10-23 13:47:23.985016

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "dc6ef21a00ef"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "tenants",
        sa.Column("id", sa.Uuid, server_default=sa.text("uuidv7()"), nullable=False),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("status", sa.Text, server_default="active", nullable=False),
        sa.Column(
            "ingest_rate_limit_per_sec",
            sa.Integer,
            server_default=sa.text("100"),
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
        sa.PrimaryKeyConstraint("id", name="tenants_pkey"),
        sa.CheckConstraint(
            "status IN ('active', 'suspended')", name="tenants_status_check"
        ),
        sa.CheckConstraint(
            "ingest_rate_limit_per_sec > 0",
            name="tenants_ingest_rate_limit_per_sec_check",
        ),
    )

    op.create_table(
        "api_keys",
        sa.Column("id", sa.Uuid, server_default=sa.text("uuidv7()"), nullable=False),
        sa.Column("tenant_id", sa.Uuid, nullable=False),
        sa.Column("name", sa.Text, nullable=False),
        # Visible part of the key, used for lookup.
        sa.Column("prefix", sa.Text, nullable=False),
        # sha256(full key).
        sa.Column("key_hash", postgresql.BYTEA, nullable=False),
        # Plain string, not sa.text(): text() would parse ":write" as a bind param.
        sa.Column(
            "scopes",
            postgresql.ARRAY(sa.Text),
            server_default="{events:write}",
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        # Updated at most once per minute.
        sa.Column("last_used_at", sa.DateTime(timezone=True)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="api_keys_pkey"),
        sa.ForeignKeyConstraint(
            ["tenant_id"], ["tenants.id"], name="api_keys_tenant_id_fkey"
        ),
        sa.UniqueConstraint("prefix", name="api_keys_prefix_key"),
        sa.CheckConstraint(
            "octet_length(key_hash) = 32", name="api_keys_key_hash_check"
        ),
    )
    op.create_index("api_keys_tenant_idx", "api_keys", ["tenant_id"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("api_keys_tenant_idx", table_name="api_keys")
    op.drop_table("api_keys")
    op.drop_table("tenants")
