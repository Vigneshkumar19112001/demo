"""add expire time in token table

Revision ID: 6cc71f4912c4
Revises: 71fe170b7d2d
Create Date: 2023-06-02 12:26:37.949485

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6cc71f4912c4'
down_revision = '71fe170b7d2d'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('refresh_tokens', sa.Column('expire_at', sa.DateTime(), nullable=False))


def downgrade() -> None:
    pass
