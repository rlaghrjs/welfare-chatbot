from app.db.database import Base, engine
from app.models.welfare_policy import WelfarePolicy


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
