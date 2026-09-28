"""Adopt the original three tables without changing or deleting their records."""
from alembic import op

revision = "0001_legacy"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""CREATE TABLE IF NOT EXISTS chat_sessions (
        id UUID PRIMARY KEY, title VARCHAR(255), status VARCHAR(20) NOT NULL,
        created_at TIMESTAMP NOT NULL DEFAULT now(), ended_at TIMESTAMP
    )""")
    op.execute("""CREATE TABLE IF NOT EXISTS chat_messages (
        id UUID PRIMARY KEY, session_id UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
        role VARCHAR(20) NOT NULL, content TEXT, message_type VARCHAR(30) NOT NULL,
        message_metadata JSONB, created_at TIMESTAMP NOT NULL DEFAULT now()
    )""")
    op.execute("""CREATE TABLE IF NOT EXISTS welfare_api_results (
        id UUID PRIMARY KEY, session_id UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
        query TEXT NOT NULL, request_url TEXT, intent JSONB, service_id VARCHAR(100),
        service_name TEXT, summary TEXT, raw_data JSONB, source VARCHAR(50) NOT NULL,
        created_at TIMESTAMP NOT NULL DEFAULT now()
    )""")


def downgrade():
    raise RuntimeError("Legacy adoption cannot be reversed automatically. Restore a reviewed backup.")
