"""add_user_security_tables

Revision ID: s1t2u3v4w5x6
Revises: p1q2r3s4t5u6, q2r3s4t5u6v7
Create Date: 2026-02-05 13:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "s1t2u3v4w5x6"
down_revision: Union[str, tuple[str, str], None] = ("p1q2r3s4t5u6", "q2r3s4t5u6v7")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 用户安全设置表
    op.create_table(
        "user_security_settings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("totp_secret", sa.String(length=255), nullable=True),
        sa.Column("is_2fa_enabled", sa.Boolean(), server_default="0", nullable=False),
        sa.Column("backup_codes", sa.JSON(), nullable=True),
        sa.Column("password_changed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("login_alert_enabled", sa.Boolean(), server_default="1", nullable=False),
        sa.Column("unusual_activity_alert", sa.Boolean(), server_default="1", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="uq_user_security_settings_user_id"),
    )
    op.create_index("ix_user_security_settings_user_id", "user_security_settings", ["user_id"], unique=True)

    # 用户设备表
    op.create_table(
        "user_devices",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("device_id", sa.String(length=255), nullable=False),
        sa.Column("device_name", sa.String(length=255), nullable=True),
        sa.Column("device_type", sa.Enum("web", "mobile", "app", name="device_type_enum"), nullable=False),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("ip_address", sa.String(length=50), nullable=True),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("first_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_current", sa.Boolean(), server_default="0", nullable=False),
        sa.Column("is_revoked", sa.Boolean(), server_default="0", nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("token_fingerprint", sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("device_id", name="uq_user_devices_device_id"),
    )
    op.create_index("ix_user_devices_user_id", "user_devices", ["user_id"], unique=False)
    op.create_index("ix_user_devices_token_fingerprint", "user_devices", ["token_fingerprint"], unique=False)

    # 用户登录审计表
    op.create_table(
        "user_login_audits",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("action", sa.Enum("login", "logout", "2fa_verify", "failed", "password_change", name="login_action_enum"), nullable=False),
        sa.Column("ip_address", sa.String(length=50), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("device_id", sa.String(length=255), nullable=True),
        sa.Column("success", sa.Boolean(), nullable=False),
        sa.Column("failure_reason", sa.String(length=255), nullable=True),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_user_login_audits_user_id", "user_login_audits", ["user_id"], unique=False)
    op.create_index("ix_user_login_audits_device_id", "user_login_audits", ["device_id"], unique=False)
    op.create_index("ix_user_login_audits_created_at", "user_login_audits", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_user_login_audits_created_at", table_name="user_login_audits")
    op.drop_index("ix_user_login_audits_device_id", table_name="user_login_audits")
    op.drop_index("ix_user_login_audits_user_id", table_name="user_login_audits")
    op.drop_table("user_login_audits")

    op.drop_index("ix_user_devices_token_fingerprint", table_name="user_devices")
    op.drop_index("ix_user_devices_user_id", table_name="user_devices")
    op.drop_table("user_devices")

    op.drop_index("ix_user_security_settings_user_id", table_name="user_security_settings")
    op.drop_table("user_security_settings")

    # 删除枚举类型
    op.execute("DROP TYPE IF EXISTS login_action_enum")
    op.execute("DROP TYPE IF EXISTS device_type_enum")