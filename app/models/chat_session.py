from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base

# 채팅 세션 DB 테이블 구조
class ChatSession(Base):
    __tablename__ = "chat_session"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_key: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(20), default="active")

    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())
    ended_at: Mapped[DateTime | None] = mapped_column(DateTime, nullable=True)

    messages = relationship("ChatMessage", back_populates="session")