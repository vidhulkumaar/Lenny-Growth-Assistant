"""add_citations_to_chat_messages

Revision ID: 03383e008969
Revises: 08208aec05dc
Create Date: 2026-10-11 12:38:07.100193

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '03383e008969'
down_revision: Union[str, Sequence[str], None] = '08208aec05dc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


from sqlalchemy.dialects import postgresql


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('chat_messages', sa.Column('citations', postgresql.JSONB(astext_type=sa.Text()), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('chat_messages', 'citations')
