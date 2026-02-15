"""merge_security_heads

Revision ID: t2u3v4w5x6y7
Revises: 177a56bc6b5a, s1t2u3v4w5x6
Create Date: 2026-02-05 16:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "t2u3v4w5x6y7"
down_revision: Union[str, tuple[str, str], None] = ("177a56bc6b5a", "s1t2u3v4w5x6")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 这是一个 merge migration，不需要执行任何操作
    # 两个父 revision 的 upgrade 已经创建了所需的表
    pass


def downgrade() -> None:
    # Merge migration 不需要 downgrade
    pass