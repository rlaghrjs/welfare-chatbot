"""Independent search statistics; no user identifiers or original messages."""
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Identity, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class SearchLog(Base):
    __tablename__ = "search_logs"
    __table_args__ = (
        Index("idx_searched_at", "searched_at"),
        Index("idx_keywords", "lifekeyword", "targetkeyword", "themekeyword"),
    )

    # SQLite requires INTEGER for generated primary keys in isolated tests.
    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), Identity(always=True), primary_key=True)
    lifekeyword: Mapped[str | None] = mapped_column(String(100))
    targetkeyword: Mapped[str | None] = mapped_column(String(100))
    themekeyword: Mapped[str | None] = mapped_column(String(100))
    age: Mapped[int | None] = mapped_column(Integer)
    searched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
