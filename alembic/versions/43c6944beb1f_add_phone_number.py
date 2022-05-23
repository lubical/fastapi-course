"""add phone number

Revision ID: 43c6944beb1f
Revises: ed00aead8981
Create Date: 2022-05-23 20:41:14.796184

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '43c6944beb1f'
down_revision = 'ed00aead8981'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('phone_number', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'phone_number')
    # ### end Alembic commands ###