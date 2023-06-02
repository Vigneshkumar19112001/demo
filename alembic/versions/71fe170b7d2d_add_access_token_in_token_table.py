"""add access token in token table

Revision ID: 71fe170b7d2d
Revises: 
Create Date: 2023-06-01 23:35:26.165612

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '71fe170b7d2d'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('refresh_tokens', sa.Column('access_token', sa.String(), nullable=False))


def downgrade() -> None:
    pass
