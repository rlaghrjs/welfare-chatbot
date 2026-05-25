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

    save_chat_message(
        db=db,
        session_id=session.id,
        role="user",
        content=request.message,
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