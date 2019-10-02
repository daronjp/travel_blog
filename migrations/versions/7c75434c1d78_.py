"""empty message

Revision ID: 7c75434c1d78
Revises: df91daa507f9
Create Date: 2019-09-29 17:06:07.214206

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7c75434c1d78'
down_revision = 'df91daa507f9'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('adventures', 'date')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('adventures', sa.Column('date', sa.VARCHAR(), autoincrement=False, nullable=True))
    # ### end Alembic commands ###
