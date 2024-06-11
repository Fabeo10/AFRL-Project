"""Added is_profile_complete to User model

Revision ID: 1da900ba6484
Revises: ec475529b0be
Create Date: 2024-06-11 09:22:20.412725

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1da900ba6484'
down_revision = 'ec475529b0be'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_profile_complete', sa.Boolean(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('is_profile_complete')

    # ### end Alembic commands ###
