from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.chat import (
    ChatRequest,
    ChatMessageResponse,
    CreateSessionResponse,
    EndSessionResponse,
)
from app.services.nlp_service import analyze_message
from app.services.welfare_service import fetch_save_and_return
from app.services.chat_session_service import (
    create_chat_session,
    get_active_session,
    save_chat_message,
    end_chat_session,
)


router = APIRouter(
    prefix="/api/chat",
    tags=["Chat"],
)


@router.post("/session", response_model=CreateSessionResponse)
def create_session(db: Session = Depends(get_db)):
    session = create_chat_session(db)

    return CreateSessionResponse(
        session_key=session.session_key,
        status=session.status,
    )


@router.post("/session/{session_key}/message", response_model=ChatMessageResponse)
async def send_message(
    session_key: str,
    request: ChatRequest,
    db: Session = Depends(get_db),
):
    session = get_active_session(db, session_key)

    if session is None:
        raise HTTPException(status_code=404, detail="활성화된 채팅 세션이 없습니다.")

    save_chat_message(
        db=db,
        session_id=session.id,
        role="user",
        content=request.message,
    )

    intent = analyze_message(request.message)

    result = await fetch_save_and_return(
        db=db,
        intent=intent,
    )

    policies = result.get("policies", [])

    if not policies:
        answer = "조건에 맞는 복지제도를 찾지 못했어요. 다른 표현으로 다시 질문해보세요."
    else:
        answer = f"관련 복지제도 {len(policies)}건을 찾았어요."

    save_chat_message(
        db=db,
        session_id=session.id,
        role="assistant",
        content=answer,
        intent=intent,
        request_url=result.get("request_url"),
    )

    return ChatMessageResponse(
        answer=answer,
        intent=intent,
        request_url=result.get("request_url"),
        saved_count=result.get("saved_count", 0),
        skipped_count=result.get("skipped_count", 0),
        policies=[
            {
                "serv_id": p.serv_id,
                "serv_nm": p.serv_nm,
                "serv_dgst": p.serv_dgst,
                "serv_dtl_link": p.serv_dtl_link,
            }
            for p in policies
        ],
    )


@router.post("/session/{session_key}/end", response_model=EndSessionResponse)
def end_session(
    session_key: str,
    db: Session = Depends(get_db),
):
    session = get_active_session(db, session_key)

    if session is None:
        raise HTTPException(status_code=404, detail="활성화된 채팅 세션이 없습니다.")

    history = end_chat_session(db, session)

    return EndSessionResponse(
        session_key=session.session_key,
        status=session.status,
        summary=history.summary,
    )