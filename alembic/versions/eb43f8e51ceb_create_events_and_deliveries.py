"""create events and deliveries

Revision ID: eb43f8e51ceb
Revises: cf517433ae2b
Create Date: 2026-10-23 13:47:24.656238

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "eb43f8e51ceb"
down_revision: str | Sequence[str] | None = "cf517433ae2b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Standard Webhooks event type: dot-delimited, [a-zA-Z0-9_],
# e.g. invoice.paid, user.profile.updated.
EVENT_TYPE_PATTERN = r"^[a-zA-Z0-9_]+(\.[a-zA-Z0-9_]+)*$"


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "events",
        # Sent as webhook-id.
        sa.Column("id", sa.Uuid, server_default=sa.text("uuidv7()"), nullable=False),
        sa.Column("tenant_id", sa.Uuid, nullable=False),
        sa.Column("event_type", sa.Text, nullable=False),
        sa.Column("payload", postgresql.BYTEA, nullable=False),
        sa.Column("idempotency_key", sa.Text, nullable=False),
        sa.Column("request_fingerprint", postgresql.BYTEA, nullable=False),
        sa.Column("traceparent", sa.Text),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="events_pkey"),
        sa.ForeignKeyConstraint(
            ["tenant_id"], ["tenants.id"], name="events_tenant_id_fkey"
        ),
        sa.UniqueConstraint(
            "tenant_id",
            "idempotency_key",
            name="events_tenant_id_idempotency_key_key",
        ),
        sa.UniqueConstraint("id", "tenant_id", name="events_id_tenant_id_key"),
        sa.CheckConstraint(
            f"event_type ~ '{EVENT_TYPE_PATTERN}'", name="events_event_type_check"
        ),
        sa.CheckConstraint(
            "octet_length(payload) <= 262144", name="events_payload_check"
        ),
        sa.CheckConstraint(
            "char_length(idempotency_key) BETWEEN 1 AND 255",
            name="events_idempotency_key_check",
        ),
        sa.CheckConstraint(
            "octet_length(request_fingerprint) = 32",
            name="events_request_fingerprint_check",
        ),
    )
    # uuidv7 is time-ordered, so id DESC means most recent first.
    op.create_index(
        "events_tenant_recent_idx", "events", ["tenant_id", sa.text("id DESC")]
    )
    op.create_index("events_retention_idx", "events", ["created_at"])

    op.create_table(
        "deliveries",
        sa.Column("id", sa.Uuid, server_default=sa.text("uuidv7()"), nullable=False),
        sa.Column("tenant_id", sa.Uuid, nullable=False),
        sa.Column("event_id", sa.Uuid, nullable=False),
        sa.Column("endpoint_id", sa.Uuid, nullable=False),
        sa.Column("status", sa.Text, server_default="pending", nullable=False),
        sa.Column(
            "attempt_count",
            sa.SmallInteger,
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column(
            "next_attempt_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("locked_until", sa.DateTime(timezone=True)),
        sa.Column("lease_token", sa.Uuid),
        sa.Column("last_status_code", sa.SmallInteger),
        sa.Column("last_error", sa.Text),
        sa.Column("delivered_at", sa.DateTime(timezone=True)),
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
        sa.PrimaryKeyConstraint("id", name="deliveries_pkey"),
        # No duplicate fan-out.
        sa.UniqueConstraint(
            "event_id", "endpoint_id", name="deliveries_event_id_endpoint_id_key"
        ),
        sa.ForeignKeyConstraint(
            ["event_id", "tenant_id"],
            ["events.id", "events.tenant_id"],
            name="deliveries_event_id_tenant_id_fkey",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["endpoint_id", "tenant_id"],
            ["endpoints.id", "endpoints.tenant_id"],
            name="deliveries_endpoint_id_tenant_id_fkey",
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'in_flight', 'retrying', 'delivered', 'dead')",
            name="deliveries_status_check",
        ),
        sa.CheckConstraint("attempt_count >= 0", name="deliveries_attempt_count_check"),
        sa.CheckConstraint(
            "(status = 'in_flight')"
            " = (lease_token IS NOT NULL AND locked_until IS NOT NULL)",
            name="deliveries_check",
        ),
        sa.CheckConstraint(
            "(status = 'delivered') = (delivered_at IS NOT NULL)",
            name="deliveries_check1",
        ),
    )
    # Dispatcher claim: SKIP LOCKED scans only due work.
    op.create_index(
        "deliveries_ready_idx",
        "deliveries",
        ["next_attempt_at"],
        postgresql_where=sa.text("status IN ('pending', 'retrying')"),
    )
    # Reaper: expired leases.
    op.create_index(
        "deliveries_leased_idx",
        "deliveries",
        ["locked_until"],
        postgresql_where=sa.text("status = 'in_flight'"),
    )
    # Management API: GET /v1/deliveries?status=dead.
    op.create_index(
        "deliveries_tenant_idx",
        "deliveries",
        ["tenant_id", "status", sa.text("created_at DESC")],
    )
    # FK lookups (Postgres does not index FKs automatically).
    op.create_index("deliveries_endpoint_idx", "deliveries", ["endpoint_id"])

    op.create_table(
        "delivery_attempts",
        sa.Column("id", sa.BigInteger, sa.Identity(always=True), nullable=False),
        sa.Column("delivery_id", sa.Uuid, nullable=False),
        sa.Column("attempt_number", sa.SmallInteger, nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("duration_ms", sa.Integer),
        sa.Column("outcome", sa.Text, nullable=False),
        sa.Column("status_code", sa.SmallInteger),
        # First 1 KB of the response body.
        sa.Column("response_excerpt", sa.Text),
        sa.Column("error_message", sa.Text),
        sa.PrimaryKeyConstraint("id", name="delivery_attempts_pkey"),
        sa.ForeignKeyConstraint(
            ["delivery_id"],
            ["deliveries.id"],
            name="delivery_attempts_delivery_id_fkey",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "delivery_id",
            "attempt_number",
            name="delivery_attempts_delivery_id_attempt_number_key",
        ),
        sa.CheckConstraint(
            "attempt_number >= 1", name="delivery_attempts_attempt_number_check"
        ),
        sa.CheckConstraint(
            "duration_ms >= 0", name="delivery_attempts_duration_ms_check"
        ),
        sa.CheckConstraint(
            "outcome IN ('success', 'http_error', 'timeout', 'connection_error',"
            " 'tls_error', 'ssrf_blocked', 'lease_expired')",
            name="delivery_attempts_outcome_check",
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("delivery_attempts")
    op.drop_index("deliveries_endpoint_idx", table_name="deliveries")
    op.drop_index("deliveries_tenant_idx", table_name="deliveries")
    op.drop_index("deliveries_leased_idx", table_name="deliveries")
    op.drop_index("deliveries_ready_idx", table_name="deliveries")
    op.drop_table("deliveries")
    op.drop_index("events_retention_idx", table_name="events")
    op.drop_index("events_tenant_recent_idx", table_name="events")
    op.drop_table("events")
