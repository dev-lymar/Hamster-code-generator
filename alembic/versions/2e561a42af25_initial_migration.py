"""Initial migration

Revision ID: 2e561a42af25
Revises: 
Create Date: 2024-08-26 21:49:57.729265

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '2e561a42af25'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###.
    op.create_table(
        'chain_cube_2048',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('promo_code', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True, server_default=sa.text('now()')),
    )

    op.create_table(
        'merge_away',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('promo_code', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True, server_default=sa.text('now()')),
    )

    op.create_table(
        'mow_and_trim',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('promo_code', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True, server_default=sa.text('now()')),
    )

    op.create_table(
        'mud_racing',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('promo_code', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True, server_default=sa.text('now()')),
    )

    op.create_table(
        'polysphere',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('promo_code', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True, server_default=sa.text('now()')),
    )

    op.create_table(
        'train_miner',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('promo_code', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True, server_default=sa.text('now()')),
    )

    op.create_table(
        'twerk_race_3d',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('promo_code', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True, server_default=sa.text('now()')),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('twerk_race_3d')
    op.drop_table('train_miner')
    op.drop_table('polysphere')
    op.drop_table('mud_racing')
    op.drop_table('mow_and_trim')
    op.drop_table('merge_away')
    op.drop_table('chain_cube_2048')
    # ### end Alembic commands ###
