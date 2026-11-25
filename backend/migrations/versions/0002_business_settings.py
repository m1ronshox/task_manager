from alembic import op
import sqlalchemy as sa

revision = "0002_business_settings"
down_revision = "0001_automotive"


def upgrade():
    op.add_column("services", sa.Column("make", sa.String(80)))
    op.create_table(
        "business_settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("phone", sa.String(24)),
        sa.Column("address", sa.String(240)),
        sa.Column("hours", sa.String(160)),
    )


def downgrade():
    raise RuntimeError("Business settings are preserved; downgrade is unavailable.")
