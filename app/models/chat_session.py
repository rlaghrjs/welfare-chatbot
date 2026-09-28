import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Index, func
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
    # NULL only for historical sessions whose owner cannot be established.
    installation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("app_installations.id", ondelete="CASCADE"), nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(),
    )
    __table_args__ = (Index("ix_chat_installation_updated", "installation_id", "updated_at"),)

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
