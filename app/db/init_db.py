from app.db.database import Base, engine
from app.models.welfare_policy import WelfarePolicy
from app.models.chat_session import ChatSession
from app.models.chat_message import ChatMessage
from app.models.chat_history import ChatHistory


def init_db() -> None:
    Base.metadata.create_all(bind=engine)