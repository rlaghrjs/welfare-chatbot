"""Add independent keyword search statistics."""
from alembic import op
import sqlalchemy as sa

revision = "0003_search_logs"
down_revision = "0002_anonymous_conditions"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "search_logs",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), primary_key=True),
        sa.Column("lifekeyword", sa.String(100), nullable=True),
        sa.Column("targetkeyword", sa.String(100), nullable=True),
        sa.Column("themekeyword", sa.String(100), nullable=True),
        sa.Column("age", sa.Integer(), nullable=True),
        sa.Column("searched_at", sa.DateTime(timezone=True), nullable=True, server_default=sa.func.now()),
    )
    op.create_index("idx_searched_at", "search_logs", ["searched_at"])
    op.create_index("idx_keywords", "search_logs", ["lifekeyword", "targetkeyword", "themekeyword"])


def downgrade():
    op.drop_index("idx_keywords", table_name="search_logs")
    op.drop_index("idx_searched_at", table_name="search_logs")
    op.drop_table("search_logs")
