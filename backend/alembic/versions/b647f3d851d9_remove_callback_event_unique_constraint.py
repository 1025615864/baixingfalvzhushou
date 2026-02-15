"""remove_callback_event_unique_constraint

Revision ID: b647f3d851d9
Revises: 90f9b6dc0269
Create Date: 2026-01-25 13:35:17.031973

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b647f3d851d9'
down_revision: Union[str, None] = '90f9b6dc0269'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Remove unique constraint on (provider, trade_no)
    # Note: explicit name 'uq_payment_cb_provider_trade_no' was used in models
    with op.batch_alter_table('payment_callback_events', schema=None) as batch_op:
        batch_op.drop_constraint('uq_payment_cb_provider_trade_no', type_='unique')


def downgrade() -> None:
    # Restore unique constraint
    with op.batch_alter_table('payment_callback_events', schema=None) as batch_op:
        batch_op.create_unique_constraint('uq_payment_cb_provider_trade_no', ['provider', 'trade_no'])

