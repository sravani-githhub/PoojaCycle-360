"""Create the initial PoojaCycle 360 relational schema."""
from alembic import op
from app.database import Base
from app import models  # noqa: F401 - registers all models on Base.metadata

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    Base.metadata.create_all(bind=op.get_bind())


def downgrade():
    Base.metadata.drop_all(bind=op.get_bind())
