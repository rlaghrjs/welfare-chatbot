import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

# 채팅 세션 DB 테이블
class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active")

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    messages = relationship(
        "ChatMessage",
        back_populates="session",
        cascade="all, delete-orphan",
    )

    api_results = relationship(
        "WelfareApiResult",
        back_populates="session",
        cascade="all, delete-orphan",
    )