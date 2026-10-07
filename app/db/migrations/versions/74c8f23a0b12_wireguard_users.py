"""Per-user WireGuard proxy settings.
Revision ID: 74c8f23a0b12
Revises: 63b7e12f9a01
"""
from alembic import op
import sqlalchemy as sa
revision = '74c8f23a0b12'
down_revision = '63b7e12f9a01'
branch_labels = None
depends_on = None

def upgrade():
    if op.get_bind().dialect.name == 'mysql':
        op.alter_column('proxies','type',existing_nullable=False,type_=sa.Enum('VMess','VLESS','Trojan','Shadowsocks','Hysteria','WireGuard'))

def downgrade():
    bind = op.get_bind()
    if bind.execute(sa.text("SELECT COUNT(*) FROM proxies WHERE type = 'WireGuard'")).scalar():
        raise RuntimeError('Remove WireGuard proxies before downgrading')
    if bind.dialect.name == 'mysql':
        op.alter_column('proxies','type',existing_nullable=False,type_=sa.Enum('VMess','VLESS','Trojan','Shadowsocks','Hysteria'))
