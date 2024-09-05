"""Added new games, Tile Trio and Fluff Crusade

Revision ID: 2535e8a8f6bf
Revises: f9a9a4e0c526
Create Date: 2024-09-04 11:53:30.844124

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2535e8a8f6bf'
down_revision: Union[str, None] = 'f9a9a4e0c526'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('fluff_crusade',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('promo_code', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_fluff_crusade_promo_code'), 'fluff_crusade', ['promo_code'], unique=False)
    op.create_table('tile_trio',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('promo_code', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_tile_trio_promo_code', 'tile_trio', ['promo_code'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('ix_tile_trio_promo_code', table_name='tile_trio')
    op.drop_table('tile_trio')
    op.drop_index(op.f('ix_fluff_crusade_promo_code'), table_name='fluff_crusade')
    op.drop_table('fluff_crusade')
    # ### end Alembic commands ###
