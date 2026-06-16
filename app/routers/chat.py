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
from app.services.local_welfare_service import fetch_local_save_and_return
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

    save_chat_message(
        db=db,
        session_id=session.id,
        role="user",
        content=request.message,
    )

    intent = analyze_message(request.message)

    if request.ctpvNm:
        intent["ctpvNm"] = request.ctpvNm

    if request.useProfile and request.profile:
        intent = merge_profile_into_intent(intent, request.profile)

    if not is_searchable_intent(intent):
        answer = (
            "복지제도를 검색하려면 대상이나 관심 분야를 조금 더 구체적으로 입력해주세요.\n"
            "예: 청년 월세 지원, 저소득층 생활비 지원, 임산부 출산 지원, 노인 돌봄 서비스"
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
            "results": {
                "central": {
                    "request_url": None,
                    "saved_count": 0,
                    "policies": [],
                },
                "local": {
                    "request_url": None,
                    "saved_count": 0,
                    "policies": [],
                },
            },
        }

    central_result = await fetch_save_and_return(
        db=db,
        session_id=session.id,
        query=request.message,
        intent=intent,
    )

    local_result = await fetch_local_save_and_return(
        db=db,
        session_id=session.id,
        query=request.message,
        intent=intent,
    )

    central_policies = central_result["policies"]
    local_policies = local_result["policies"]

    answer = (
        f"중앙 복지제도 {len(central_policies)}건, "
        f"지자체 복지제도 {len(local_policies)}건을 찾았어요."
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
        "results": {
            "central": {
                "request_url": central_result["request_url"],
                "saved_count": central_result["saved_count"],
                "policies": central_policies,
            },
            "local": {
                "request_url": local_result["request_url"],
                "saved_count": local_result["saved_count"],
                "policies": local_policies,
            },
        },
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

def is_searchable_intent(intent: dict) -> bool:
    searchable_keys = [
        "searchWrd",
        "lifeArray",
        "trgterIndvdlArray",
        "intrsThemaArray",
        "age",
    ]

    return any(intent.get(key) for key in searchable_keys)

def merge_profile_into_intent(intent: dict, profile) -> dict:
    if profile is None:
        return intent

    # 질문에서 나이가 추출되지 않았을 때만 프로필 나이 사용
    if not intent.get("age") and profile.age:
        intent["age"] = profile.age

    # 질문에서 생애주기가 추출되지 않았을 때만 프로필 생애주기 사용
    if not intent.get("lifeArray") and profile.lifeArray:
        intent["lifeArray"] = profile.lifeArray

    # 질문에서 가구상황이 추출되지 않았을 때만 프로필 가구상황 사용
    if not intent.get("trgterIndvdlArray") and profile.trgterIndvdlArray:
        intent["trgterIndvdlArray"] = profile.trgterIndvdlArray

    # 질문에서 관심주제가 추출되지 않았을 때만 프로필 관심주제 사용
    if not intent.get("intrsThemaArray") and profile.intrsThemaArray:
        intent["intrsThemaArray"] = profile.intrsThemaArray

    return intent