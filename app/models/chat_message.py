from sqlalchemy import ForeignKey, String, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base


# 채팅 메세지 DB 테이블 구조
class ChatMessage(Base):
    __tablename__ = "chat_message"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    session_id: Mapped[int] = mapped_column(ForeignKey("chat_session.id"))
    role: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text)

    intent_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    request_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())

    session = relationship("ChatSession", back_populates="messages")