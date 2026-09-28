"""Anonymous ownership and the policy/subscription catalog; retain legacy data."""
from pathlib import Path
from alembic import op

revision = "0002_anonymous_conditions"
down_revision = "0001_legacy"
branch_labels = None
depends_on = None


def upgrade():
    # Frozen DDL belongs to this revision; never import evolving ORM models here.
    sql = (Path(__file__).parent / "0002_tables.sql").read_text(encoding="utf-8")
    for statement in sql.split(";"):
        if statement.strip():
            op.execute(statement)
    op.execute("ALTER TABLE chat_sessions ADD COLUMN installation_id UUID REFERENCES app_installations(id) ON DELETE CASCADE")
    op.execute("ALTER TABLE chat_sessions ADD COLUMN updated_at TIMESTAMPTZ NOT NULL DEFAULT now()")
    # Original create_all columns were timezone-naive; do not guess their timezone.
    # Leave archived timestamps untouched, and use migration time for ordering old sessions.
    op.execute("ALTER TABLE chat_sessions RENAME COLUMN status TO legacy_status")
    op.execute("ALTER TABLE chat_sessions ALTER COLUMN legacy_status DROP NOT NULL")
    op.execute("ALTER TABLE chat_sessions RENAME COLUMN ended_at TO legacy_ended_at")
    op.execute("CREATE INDEX ix_chat_installation_updated ON chat_sessions (installation_id, updated_at)")
    op.execute("ALTER TABLE chat_messages ADD COLUMN sequence_no INTEGER")
    op.execute("""WITH ordered AS (
        SELECT id, row_number() OVER (PARTITION BY session_id ORDER BY created_at, id) AS position
        FROM chat_messages
    ) UPDATE chat_messages SET sequence_no = ordered.position FROM ordered WHERE chat_messages.id = ordered.id""")
    op.execute("ALTER TABLE chat_messages ALTER COLUMN sequence_no SET NOT NULL")
    op.execute("ALTER TABLE chat_messages ADD CONSTRAINT uq_chat_message_sequence UNIQUE (session_id, sequence_no)")


def downgrade():
    raise RuntimeError("This migration preserves history. Use a reviewed backup rather than dropping catalog data.")
