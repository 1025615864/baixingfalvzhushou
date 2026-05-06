"""Alembic migration for new common tables

Revision ID: 001_add_common_tables
Revises: 
Create Date: 2026-05-06
"""
from alembic import op
import sqlalchemy as sa

revision = "001_add_common_tables"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("service", sa.String(50), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("user_role", sa.String(50), nullable=True),
        sa.Column("action", sa.String(50), nullable=True),
        sa.Column("resource_type", sa.String(50), nullable=True),
        sa.Column("resource_id", sa.Integer(), nullable=True),
        sa.Column("changes", sa.JSON(), nullable=True),
        sa.Column("ip_address", sa.String(50), nullable=True),
        sa.Column("user_agent", sa.String(500), nullable=True),
        sa.Column("request_id", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_logs_service", "audit_logs", ["service"], unique=False)
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"], unique=False)
    op.create_index("ix_audit_logs_request_id", "audit_logs", ["request_id"], unique=False)
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"], unique=False)
    op.create_index("ix_audit_service_resource", "audit_logs", ["service", "resource_type", "resource_id"], unique=False)
    op.create_index("ix_audit_user_time", "audit_logs", ["user_id", "created_at"], unique=False)
    op.create_index("ix_audit_action_time", "audit_logs", ["action", "created_at"], unique=False)

    op.create_table(
        "saga_execution_logs",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("saga_type", sa.String(50), nullable=True),
        sa.Column("status", sa.String(20), nullable=True),
        sa.Column("correlation_id", sa.String(50), nullable=True),
        sa.Column("current_step", sa.Integer(), nullable=True),
        sa.Column("total_steps", sa.Integer(), nullable=True),
        sa.Column("steps_log", sa.JSON(), nullable=True),
        sa.Column("error_message", sa.String(500), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_saga_execution_logs_saga_type", "saga_execution_logs", ["saga_type"], unique=False)
    op.create_index("ix_saga_execution_logs_status", "saga_execution_logs", ["status"], unique=False)
    op.create_index("ix_saga_execution_logs_correlation_id", "saga_execution_logs", ["correlation_id"], unique=False)
    op.create_index("ix_saga_execution_logs_created_at", "saga_execution_logs", ["created_at"], unique=False)
    op.create_index("ix_saga_type_status", "saga_execution_logs", ["saga_type", "status"], unique=False)
    op.create_index("ix_saga_correlation", "saga_execution_logs", ["correlation_id"], unique=False)

    op.create_table(
        "outbox_messages",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("aggregate_type", sa.String(50), nullable=True),
        sa.Column("aggregate_id", sa.String(50), nullable=True),
        sa.Column("event_type", sa.String(50), nullable=True),
        sa.Column("topic", sa.String(100), nullable=False),
        sa.Column("payload", sa.Text(), nullable=False),
        sa.Column("key", sa.String(100), nullable=True),
        sa.Column("status", sa.String(20), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=True),
        sa.Column("max_retries", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.String(500), nullable=True),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_outbox_messages_aggregate_type", "outbox_messages", ["aggregate_type"], unique=False)
    op.create_index("ix_outbox_messages_aggregate_id", "outbox_messages", ["aggregate_id"], unique=False)
    op.create_index("ix_outbox_messages_event_type", "outbox_messages", ["event_type"], unique=False)
    op.create_index("ix_outbox_messages_status", "outbox_messages", ["status"], unique=False)
    op.create_index("ix_outbox_messages_created_at", "outbox_messages", ["created_at"], unique=False)
    op.create_index("ix_outbox_status_created", "outbox_messages", ["status", "created_at"], unique=False)
    op.create_index("ix_outbox_aggregate", "outbox_messages", ["aggregate_type", "aggregate_id"], unique=False)
    op.create_index("ix_outbox_topic_status", "outbox_messages", ["topic", "status"], unique=False)

    op.create_table(
        "jwt_keys",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("secret", sa.String(256), nullable=False),
        sa.Column("algorithm", sa.String(20), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("rotated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("version"),
    )

    op.create_table(
        "password_history",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("password_hash", sa.String(128), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade():
    op.drop_table("password_history")
    op.drop_table("jwt_keys")
    op.drop_table("outbox_messages")
    op.drop_table("saga_execution_logs")
    op.drop_table("audit_logs")
