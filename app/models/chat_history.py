# models/chat_history.py

from sqlalchemy import ForeignKey, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.db.database import Base


# 채팅 기록 DB 테이블 구조
class ChatHistory(Base):
    __tablename__ = "chat_history"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    session_id: Mapped[int] = mapped_column(ForeignKey("chat_session.id"), unique=True)

    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    full_history: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())