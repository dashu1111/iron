"""add overtime pay fields

Revision ID: c8f3a1b2d4e5
Revises: 2556e9e82eee
Create Date: 2026-06-01 23:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'c8f3a1b2d4e5'
down_revision = '2556e9e82eee'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('overtimes', schema=None) as batch_op:
        batch_op.add_column(sa.Column('quantity', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('amount', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('submitter_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_overtimes_submitter_id', 'users', ['submitter_id'], ['id'])


def downgrade():
    with op.batch_alter_table('overtimes', schema=None) as batch_op:
        batch_op.drop_constraint('fk_overtimes_submitter_id', type_='foreignkey')
        batch_op.drop_column('submitter_id')
        batch_op.drop_column('amount')
        batch_op.drop_column('quantity')
