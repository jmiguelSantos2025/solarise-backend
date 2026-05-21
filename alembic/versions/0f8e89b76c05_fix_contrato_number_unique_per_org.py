"""fix_contrato_number_unique_per_org

Revision ID: 0f8e89b76c05
Revises: b3f2a8d9e1c5
Create Date: 2026-05-21 16:33:57.782802

"""
from typing import Sequence, Union

from alembic import op

revision: str = '0f8e89b76c05'
down_revision: Union[str, Sequence[str], None] = 'b3f2a8d9e1c5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint('contratos_number_key', 'contratos', type_='unique')
    op.create_unique_constraint('uq_contrato_org_number', 'contratos', ['organization_id', 'number'])


def downgrade() -> None:
    op.drop_constraint('uq_contrato_org_number', 'contratos', type_='unique')
    op.create_unique_constraint('contratos_number_key', 'contratos', ['number'])
