from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.chat_session import ChatSession
from app.models.chat_message import ChatMessage


def create_chat_session(db: Session, installation_id: UUID, title: str) -> ChatSession:
    session = ChatSession(
        title=title[:255],
        installation_id=installation_id,
    )

    db.add(session)
    db.flush()

    return session


def get_owned_session(db: Session, session_id: UUID, installation_id: UUID) -> ChatSession | None:
    return (
        db.query(ChatSession)
        .filter(ChatSession.id == session_id)
        .filter(ChatSession.installation_id == installation_id)
        .first()
    )


def save_chat_message(
    db: Session,
    session_id,
    role: str,
    content: str | None,
    message_type: str = "text",
    message_metadata: dict | None = None,
):
    # Serialize writers within a chat and persist an explicit, clock-independent order.
    session = db.query(ChatSession).filter_by(id=session_id).with_for_update().one()
    last_sequence = db.query(func.max(ChatMessage.sequence_no)).filter_by(session_id=session_id).scalar() or 0
    message = ChatMessage(
        session_id=session_id,
        role=role,
        sequence_no=last_sequence + 1,
        content=content,
        message_type=message_type,
        message_metadata=message_metadata,
    )

    db.add(message)
    session.updated_at = datetime.now(timezone.utc)
    db.flush()

    return message
