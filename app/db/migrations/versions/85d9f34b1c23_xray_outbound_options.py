"""Store client outbound options independently from transport and protocol."""
from alembic import op
import sqlalchemy as sa
revision = '85d9f34b1c23'
down_revision = '74c8f23a0b12'
branch_labels = None
depends_on = None
def upgrade():
    op.add_column('hosts', sa.Column('xray_outbound_settings', sa.JSON(), nullable=True))
def downgrade():
    op.drop_column('hosts', 'xray_outbound_settings')
