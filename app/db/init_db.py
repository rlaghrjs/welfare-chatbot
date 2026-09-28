from pathlib import Path
from sqlalchemy import inspect, text
from alembic.config import Config
from alembic.script import ScriptDirectory
from app.db.database import engine


def init_db() -> None:
    """Fail clearly on an old schema instead of silently starting an incompatible app."""
    config = Config(str(Path(__file__).resolve().parents[2] / "alembic.ini"))
    head = ScriptDirectory.from_config(config).get_current_head()
    with engine.connect() as connection:
        if "alembic_version" not in inspect(connection).get_table_names():
            raise RuntimeError("DB 초기화가 필요합니다. python -m alembic upgrade head 를 실행해주세요.")
        revision = connection.execute(text("SELECT version_num FROM alembic_version")).scalar()
        if revision != head:
            raise RuntimeError("DB 구조 업데이트가 필요합니다. python -m alembic upgrade head 를 실행해주세요.")
