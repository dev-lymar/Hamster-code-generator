"""Added new game Bouncemasters

Revision ID: 652b3b420c9f
Revises: c4e02ccd4113
Create Date: 2024-09-12 13:12:24.164563

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '652b3b420c9f'
down_revision: Union[str, None] = 'c4e02ccd4113'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('bouncemasters',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('promo_code', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_bouncemasters_created_at', 'bouncemasters', ['created_at'], unique=False)
    op.create_index('ix_bouncemasters_promo_code', 'bouncemasters', ['promo_code'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('ix_bouncemasters_promo_code', table_name='bouncemasters')
    op.drop_index('ix_bouncemasters_created_at', table_name='bouncemasters')
    op.drop_table('bouncemasters')
    # ### end Alembic commands ###
