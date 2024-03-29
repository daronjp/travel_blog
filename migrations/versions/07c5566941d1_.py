"""empty message

Revision ID: 07c5566941d1
Revises: 2731655ba8ba
Create Date: 2019-09-29 18:08:35.219135

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '07c5566941d1'
down_revision = '2731655ba8ba'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('photos', 'published')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('photos', sa.Column('published', sa.VARCHAR(), autoincrement=False, nullable=True))
    # ### end Alembic commands ###
