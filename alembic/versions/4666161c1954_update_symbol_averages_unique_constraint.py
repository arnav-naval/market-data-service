"""update_symbol_averages_unique_constraint

Revision ID: 4666161c1954
Revises: 6c3e2b197283
Create Date: 2025-06-25 23:50:39.987836

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4666161c1954'
down_revision: Union[str, Sequence[str], None] = '6c3e2b197283'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Drop the old unique constraint and index
    op.drop_constraint('uq_symbol_interval_timestamp', 'symbol_averages', type_='unique')
    op.drop_index('ix_ma_symbol_interval_ts', table_name='symbol_averages')
    
    # Create the new unique constraint and index for just symbol
    op.create_unique_constraint('uq_symbol', 'symbol_averages', ['symbol'])
    op.create_index('ix_ma_symbol', 'symbol_averages', ['symbol'])


def downgrade() -> None:
    """Downgrade schema."""
    # Drop the new unique constraint and index
    op.drop_constraint('uq_symbol', 'symbol_averages', type_='unique')
    op.drop_index('ix_ma_symbol', table_name='symbol_averages')
    
    # Recreate the old unique constraint and index
    op.create_unique_constraint('uq_symbol_interval_timestamp', 'symbol_averages', ['symbol', 'interval', 'timestamp'])
    op.create_index('ix_ma_symbol_interval_ts', 'symbol_averages', ['symbol', 'interval', 'timestamp'])
