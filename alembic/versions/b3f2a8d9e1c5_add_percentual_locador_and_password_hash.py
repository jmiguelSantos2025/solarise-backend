"""add percentual_locador and password_hash

Revision ID: b3f2a8d9e1c5
Revises: ae93f1168778
Create Date: 2026-05-15

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'b3f2a8d9e1c5'
down_revision: Union[str, Sequence[str], None] = 'ae93f1168778'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('contratos',
        sa.Column('percentual_locador', sa.Numeric(precision=5, scale=4), nullable=True)
    )
    op.add_column('users',
        sa.Column('password_hash', sa.String(length=255), nullable=True)
    )


def downgrade() -> None:
    op.drop_column('contratos', 'percentual_locador')
    op.drop_column('users', 'password_hash')
