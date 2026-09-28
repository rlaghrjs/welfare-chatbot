from alembic import context
from sqlalchemy import create_engine, pool
from app.core.config import settings
from app.db.database import Base
import app.models  # noqa: F401 - register the complete metadata

config = context.config
target_metadata = Base.metadata

if context.is_offline_mode():
    context.configure(url=settings.database_url, target_metadata=target_metadata,
                      literal_binds=True, dialect_opts={"paramstyle": "named"})
    with context.begin_transaction():
        context.run_migrations()
else:
    provided = config.attributes.get("connection")
    def migrate(connection):
        context.configure(connection=connection, target_metadata=target_metadata,
                          compare_type=True)
        with context.begin_transaction():
            context.run_migrations()
    if provided is not None:
        migrate(provided)
    else:
        engine = create_engine(settings.database_url, poolclass=pool.NullPool)
        with engine.connect() as connection:
            migrate(connection)
