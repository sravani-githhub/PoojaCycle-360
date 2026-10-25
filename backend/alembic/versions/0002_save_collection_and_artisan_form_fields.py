"""Persist fields already collected by the collection and artisan forms."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "0002_form_fields"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def _columns(table_name):
    return {column["name"] for column in inspect(op.get_bind()).get_columns(table_name)}


def upgrade():
    # The initial prototype migration builds metadata dynamically. These guards
    # keep this migration compatible with both fresh and already-created DBs.
    waste_columns = _columns("waste_reports")
    if "preferred_pickup_window" not in waste_columns:
        op.add_column("waste_reports", sa.Column("preferred_pickup_window", sa.String(length=12), nullable=True))
    if "festival_collection" not in waste_columns:
        op.add_column("waste_reports", sa.Column("festival_collection", sa.Boolean(), server_default=sa.false(), nullable=False))

    artisan_columns = _columns("artisans")
    if "contact_email" not in artisan_columns:
        op.add_column("artisans", sa.Column("contact_email", sa.String(length=254), nullable=True))
    if "monthly_capacity_kg" not in artisan_columns:
        op.add_column("artisans", sa.Column("monthly_capacity_kg", sa.Numeric(12, 3), nullable=True))


def downgrade():
    artisan_columns = _columns("artisans")
    if "monthly_capacity_kg" in artisan_columns:
        op.drop_column("artisans", "monthly_capacity_kg")
    if "contact_email" in artisan_columns:
        op.drop_column("artisans", "contact_email")

    waste_columns = _columns("waste_reports")
    if "festival_collection" in waste_columns:
        op.drop_column("waste_reports", "festival_collection")
    if "preferred_pickup_window" in waste_columns:
        op.drop_column("waste_reports", "preferred_pickup_window")
