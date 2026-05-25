import json
import uuid

from datetime import datetime
from sqlalchemy.orm import Session
from app.models.chat_session import ChatSession
from app.models.chat_message import ChatMessage
from app.models.chat_history import ChatHistory


# 채팅 세션 생성
def create_chat_session(db: Session) -> ChatSession:
    session = ChatSession(
        session_key=str(uuid.uuid4()),
        status="active",
    )

    db.add(session)
    db.commit()
    db.refresh(session)

    return session


def get_active_session(db: Session, session_key: str) -> ChatSession | None:
    return (
        db.query(ChatSession)
        .filter(ChatSession.session_key == session_key)
        .filter(ChatSession.status == "active")
        .first()
    )


# 채팅 데이터 저장
def save_chat_message(
    db: Session,
    session_id: int,
    role: str,
    content: str,
    intent: dict | None = None,
    request_url: str | None = None,
) -> ChatMessage:
    message = ChatMessage(
        session_id=session_id,
        role=role,
        content=content,
        intent_json=json.dumps(intent, ensure_ascii=False) if intent else None,
        request_url=request_url,
    )

    db.add(message)
    db.commit()
    db.refresh(message)

    return message


# 채팅 기록 저장
def end_chat_session(db: Session, session: ChatSession) -> ChatHistory:
    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session.id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )

    full_history = "\n".join(
        [f"{m.role}: {m.content}" for m in messages]
    )

    summary = make_simple_summary(messages)

    history = ChatHistory(
        session_id=session.id,
        full_history=full_history,
        summary=summary,
    )

    session.status = "ended"
    session.ended_at = datetime.now()

    db.add(history)
    db.commit()
    db.refresh(history)

    return history


def make_simple_summary(messages: list[ChatMessage]) -> str:
    user_messages = [m.content for m in messages if m.role == "user"]

    if not user_messages:
        return "대화 내용 없음"

    return f"사용자가 총 {len(user_messages)}개의 질문을 했습니다. 주요 질문: {user_messages[0]}"