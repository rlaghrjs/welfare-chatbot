from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.chat import ChatRequest
from app.services.chat_session_service import (
    create_chat_session,
    get_active_session,
    save_chat_message,
    end_chat_session,
)
from app.services.nlp_service import analyze_message
from app.services.welfare_service import fetch_save_and_return
from app.models.chat_session import ChatSession
from app.models.chat_message import ChatMessage
from app.models.welfare_api_result import WelfareApiResult


router = APIRouter(
    prefix="/api/chat",
    tags=["Chat"],
)


@router.post("/session")
def create_session(db: Session = Depends(get_db)):
    session = create_chat_session(db)

    return {
        "session_id": str(session.id),
        "title": session.title,
        "status": session.status,
    }


@router.post("/session/{session_id}/message")
async def send_message(
    session_id: UUID,
    request: ChatRequest,
    db: Session = Depends(get_db),
):
    session = get_active_session(db, session_id)

    if session is None:
        raise HTTPException(status_code=404, detail="활성 세션이 없습니다.")

    if session.title == "새 채팅":
        session.title = request.message[:30]
        db.commit()
        db.refresh(session)

    save_chat_message(
        db=db,
        session_id=session.id,
        role="user",
        content=request.message,
        message_type="text",
    )

    intent = analyze_message(request.message)

    result = await fetch_save_and_return(
        db=db,
        session_id=session.id,
        query=request.message,
        intent=intent,
    )

    policies = result["policies"]

    answer = (
        f"관련 복지제도 {len(policies)}건을 찾았어요."
        if policies
        else "조건에 맞는 복지제도를 찾지 못했어요."
    )

    save_chat_message(
        db=db,
        session_id=session.id,
        role="assistant",
        content=answer,
        message_type="text",
    )

    if policies:
        save_chat_message(
            db=db,
            session_id=session.id,
            role="assistant",
            content=None,
            message_type="welfare_cards",
            message_metadata={
                "policies": policies
            },
        )

    return {
        "answer": answer,
        "intent": intent,
        "request_url": result["request_url"],
        "saved_count": result["saved_count"],
        "policies": policies,
    }


@router.post("/session/{session_id}/end")
def end_session(
    session_id: UUID,
    db: Session = Depends(get_db),
):
    session = get_active_session(db, session_id)

    if session is None:
        raise HTTPException(status_code=404, detail="활성 세션이 없습니다.")

    ended = end_chat_session(db, session)

    return {
        "session_id": str(ended.id),
        "status": ended.status,
        "ended_at": ended.ended_at,
    }


@router.get("/sessions")
def get_sessions(db: Session = Depends(get_db)):
    sessions = (
        db.query(ChatSession)
        .order_by(ChatSession.created_at.desc())
        .all()
    )

    return [
        {
            "session_id": str(session.id),
            "title": session.title,
            "status": session.status,
            "created_at": session.created_at,
            "ended_at": session.ended_at,
        }
        for session in sessions
    ]


@router.get("/session/{session_id}")
def get_session_detail(
    session_id: UUID,
    db: Session = Depends(get_db),
):
    session = (
        db.query(ChatSession)
        .filter(ChatSession.id == session_id)
        .first()
    )

    if session is None:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")

    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session.id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )

    api_results = (
        db.query(WelfareApiResult)
        .filter(WelfareApiResult.session_id == session.id)
        .order_by(WelfareApiResult.created_at.asc())
        .all()
    )

    return {
        "session": {
            "session_id": str(session.id),
            "title": session.title,
            "status": session.status,
            "created_at": session.created_at,
            "ended_at": session.ended_at,
        },
        "messages": [
            {
                "id": str(message.id),
                "role": message.role,
                "content": message.content,
                "message_type": message.message_type,
                "message_metadata": message.message_metadata,
                "created_at": message.created_at,
            }
            for message in messages
        ],
        "api_results": [
            {
                "id": str(result.id),
                "query": result.query,
                "request_url": result.request_url,
                "intent": result.intent,
                "service_id": result.service_id,
                "service_name": result.service_name,
                "summary": result.summary,
                "raw_data": result.raw_data,
                "created_at": result.created_at,
            }
            for result in api_results
        ],
    }