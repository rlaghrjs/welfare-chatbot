from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.chat_session import ChatSession
from app.models.chat_message import ChatMessage


def create_chat_session(db: Session, title: str | None = None) -> ChatSession:
    session = ChatSession(
        title=title or "새 채팅",
        status="active",
    )

    db.add(session)
    db.commit()
    db.refresh(session)

    return session


def get_active_session(db: Session, session_id: UUID) -> ChatSession | None:
    return (
        db.query(ChatSession)
        .filter(ChatSession.id == session_id)
        .filter(ChatSession.status == "active")
        .first()
    )


def save_chat_message(
    db: Session,
    session_id: UUID,
    role: str,
    content: str,
) -> ChatMessage:
    message = ChatMessage(
        session_id=session_id,
        role=role,
        content=content,
    )

    db.add(message)
    db.commit()
    db.refresh(message)

    return message


def end_chat_session(db: Session, session: ChatSession) -> ChatSession:
    session.status = "ended"
    session.ended_at = datetime.now()

    db.commit()
    db.refresh(session)

    return session