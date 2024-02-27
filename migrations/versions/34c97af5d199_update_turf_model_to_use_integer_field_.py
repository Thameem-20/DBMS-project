"""Update Turf model to use Integer field for phone number

Revision ID: 34c97af5d199
Revises: 745a2d3dd6e3
Create Date: 2024-02-27 07:23:50.783137

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '34c97af5d199'
down_revision = '745a2d3dd6e3'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('turf', schema=None) as batch_op:
        batch_op.alter_column('turf_phone',
               existing_type=sa.VARCHAR(length=15),
               type_=sa.Integer(),
               existing_nullable=True)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('turf', schema=None) as batch_op:
        batch_op.alter_column('turf_phone',
               existing_type=sa.Integer(),
               type_=sa.VARCHAR(length=15),
               existing_nullable=True)

    # ### end Alembic commands ###