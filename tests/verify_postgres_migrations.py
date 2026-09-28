"""Optional real PostgreSQL test: python -m tests.verify_postgres_migrations.

Uses .env DATABASE_URL, creates a unique schema inside a transaction and always
rolls it back. Existing schemas/records are never changed. Requires CREATE SCHEMA.
Run directly as `python tests/verify_postgres_migrations.py` from the project root
with the project on PYTHONPATH, or `python -m tests.verify_postgres_migrations`.
"""
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text
from app.core.config import settings


def main():
    engine = create_engine(settings.database_url, connect_args={"connect_timeout": 5}, echo=False)
    if engine.dialect.name != "postgresql":
        raise RuntimeError("This verification requires PostgreSQL.")
    with engine.connect() as conn:
        transaction = conn.begin()
        try:
            schema = "welfare_test_" + uuid.uuid4().hex
            conn.execute(text(f'CREATE SCHEMA "{schema}"'))
            conn.execute(text(f'SET LOCAL search_path TO "{schema}"'))
            config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
            config.attributes["connection"] = conn
            command.upgrade(config, "0001_legacy")
            session_id, message_id = uuid.uuid4(), uuid.uuid4()
            conn.execute(text("INSERT INTO chat_sessions (id,title,status) VALUES (:id,'historical','ended')"), {"id": session_id})
            conn.execute(text("INSERT INTO chat_messages (id,session_id,role,content,message_type) VALUES (:id,:session,'user','historical','text')"), {"id": message_id, "session": session_id})
            command.upgrade(config, "head")
            inspector = inspect(conn)
            assert len(inspector.get_table_names()) == 14  # 12 core + legacy results + Alembic
            row = conn.execute(text("SELECT installation_id,legacy_status FROM chat_sessions WHERE id=:id"), {"id": session_id}).one()
            assert row[0] is None and row[1] == "ended"
            assert conn.execute(text("SELECT sequence_no FROM chat_messages WHERE id=:id"), {"id": message_id}).scalar() == 1
            command.upgrade(config, "head")  # No duplicate tables/columns on rerun.
            print("PASS: PostgreSQL migration, legacy preservation and repeat upgrade.")
        finally:
            transaction.rollback()
    engine.dispose()
    print("PASS: temporary schema rolled back; existing database unchanged.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"FAIL: {type(exc).__name__}. Check PostgreSQL connectivity and CREATE SCHEMA permission.")
        raise SystemExit(1)
