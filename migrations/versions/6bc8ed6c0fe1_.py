"""empty message

Revision ID: 6bc8ed6c0fe1
Revises: 53743c179780
Create Date: 2024-06-11 16:53:01.967541

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6bc8ed6c0fe1'
down_revision = '53743c179780'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('companies', schema=None) as batch_op:
        batch_op.add_column(sa.Column('image', sa.String(length=75), nullable=True))

    with op.batch_alter_table('services', schema=None) as batch_op:
        batch_op.add_column(sa.Column('image', sa.String(length=75), nullable=True))

    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('image', sa.String(length=75), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('image')

    with op.batch_alter_table('services', schema=None) as batch_op:
        batch_op.drop_column('image')

    with op.batch_alter_table('companies', schema=None) as batch_op:
        batch_op.drop_column('image')

    # ### end Alembic commands ###
