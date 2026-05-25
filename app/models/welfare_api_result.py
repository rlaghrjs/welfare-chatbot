import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

#복지 데이터 DB 테이블
class WelfareApiResult(Base):
    __tablename__ = "welfare_api_results"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )

    query: Mapped[str] = mapped_column(Text, nullable=False)

    request_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    intent: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    service_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    service_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    raw_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    source: Mapped[str] = mapped_column(
        String(50),
        default="welfare_openapi",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
    )

    session = relationship("ChatSession", back_populates="api_results")