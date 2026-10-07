"""Xray v26.3.27 client configuration and Hysteria users.

Revision ID: 63b7e12f9a01
Revises: 2b231de97dc3
"""
from alembic import op
import sqlalchemy as sa

revision = "63b7e12f9a01"
down_revision = "2b231de97dc3"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("hosts", sa.Column("xray_stream_settings", sa.JSON(), nullable=True))
    op.add_column("hosts", sa.Column("xray_protocol_settings", sa.JSON(), nullable=True))
    # SQLite stores Enum as VARCHAR; MySQL uses a native enum of member names.
    if op.get_bind().dialect.name == "mysql":
        op.alter_column("proxies", "type", existing_nullable=False,
                        type_=sa.Enum("VMess", "VLESS", "Trojan", "Shadowsocks", "Hysteria"))


def downgrade():
    bind = op.get_bind()
    if bind.execute(sa.text("SELECT COUNT(*) FROM proxies WHERE type = 'Hysteria'")).scalar():
        raise RuntimeError("Remove Hysteria proxies before downgrading")
    if bind.dialect.name == "mysql":
        op.alter_column("proxies", "type", existing_nullable=False,
                        type_=sa.Enum("VMess", "VLESS", "Trojan", "Shadowsocks"))
    op.drop_column("hosts", "xray_protocol_settings")
    op.drop_column("hosts", "xray_stream_settings")
