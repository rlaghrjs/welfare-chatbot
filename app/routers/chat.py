from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.chat import ChatRequest
from app.services.chat_session_service import create_chat_session, get_owned_session, save_chat_message
from app.services.installation_service import require_installation
from app.services.nlp_service import analyze_message
from app.services.welfare_service import build_welfare_params, parse_welfare_xml, build_request_url
from app.services.local_welfare_service import build_local_welfare_params, parse_local_welfare_xml, build_local_request_url
from app.services.welfare_api_common import fetch_xml
from app.core.config import settings
from app.models.chat_session import ChatSession
from app.models.chat_message import ChatMessage
from app.models.platform import AppInstallation

router = APIRouter(prefix="/api/chat", tags=["Chat"])


def session_data(session):
    return {"session_id": str(session.id), "title": session.title,
            "created_at": session.created_at, "updated_at": session.updated_at}


def is_searchable_intent(intent: dict) -> bool:
    return any(intent.get(k) for k in (
        "searchWrd", "lifeArray", "trgterIndvdlArray", "intrsThemaArray", "age",
    )) or intent.get("age") == 0


def merge_profile_into_intent(intent: dict, profile) -> dict:
    if profile is not None:
        for key in ("age", "lifeArray", "trgterIndvdlArray", "intrsThemaArray"):
            if intent.get(key) in (None, "") and getattr(profile, key) is not None:
                intent[key] = getattr(profile, key)
    return intent


@router.post("/message")
async def send_message(request: ChatRequest,
                       installation: AppInstallation = Depends(require_installation),
                       db: Session = Depends(get_db)):
    session = None
    if request.session_id:
        session = get_owned_session(db, request.session_id, installation.id)
        if session is None:
            raise HTTPException(404, "채팅을 찾을 수 없습니다.")

    # Fetch before persisting: provider failures cannot leave an empty/unknown session.
    intent = analyze_message(request.message)
    if request.ctpvNm:
        intent["ctpvNm"] = request.ctpvNm
    if request.useProfile:
        intent = merge_profile_into_intent(intent, request.profile)
    results = {key: {"request_url": None, "saved_count": 0, "policies": []}
               for key in ("central", "local")}
    if is_searchable_intent(intent):
        for key, url, build, parse, safe_url in (
            ("central", settings.welfare_api_url, build_welfare_params, parse_welfare_xml, build_request_url),
            ("local", settings.local_welfare_api_url, build_local_welfare_params, parse_local_welfare_xml, build_local_request_url),
        ):
            params = build(intent)
            policies = parse(await fetch_xml(url, params))

            limit = 2 if key == "central" else 3
            policies = policies[:limit]

            results[key] = {"request_url": safe_url(params), "saved_count": len(policies), "policies": policies}

        answer = f"중앙 복지제도 {len(results['central']['policies'])}건, 지자체 복지제도 {len(results['local']['policies'])}건을 찾았어요."
    else:
        answer = "대상이나 관심 분야를 조금 더 구체적으로 입력해주세요. 예: 청년 월세 지원, 노인 돌봄 서비스"

    try:
        if session is None:
            session = create_chat_session(db, installation.id, request.message)
        save_chat_message(db, session.id, "user", request.message)
        save_chat_message(db, session.id, "assistant", answer, message_metadata={"intent": intent})
        # Preserve exactly the cards shown, including across app restarts. The future
        # catalog collector will replace these transitional snapshots with version links.
        for key, title in (("central", "중앙 복지제도"), ("local", "지자체 복지제도")):
            if results[key]["policies"]:
                save_chat_message(db, session.id, "assistant", None, "welfare_cards", {
                    "title": title, "policies": results[key]["policies"],
                    "requestUrl": results[key]["request_url"],
                })
        db.commit()
    except Exception:
        db.rollback()
        raise
    return {"session_id": str(session.id), "title": session.title,
            "answer": answer, "intent": intent, "results": results}


@router.get("/sessions")
def get_sessions(installation: AppInstallation = Depends(require_installation), db: Session = Depends(get_db)):
    sessions = db.query(ChatSession).filter(ChatSession.installation_id == installation.id).order_by(ChatSession.updated_at.desc()).all()
    return [session_data(s) for s in sessions]


@router.get("/session/{session_id}")
def get_session_detail(session_id: UUID, installation: AppInstallation = Depends(require_installation), db: Session = Depends(get_db)):
    session = get_owned_session(db, session_id, installation.id)
    if session is None:
        raise HTTPException(404, "채팅을 찾을 수 없습니다.")
    messages = db.query(ChatMessage).filter(ChatMessage.session_id == session.id).order_by(ChatMessage.sequence_no).all()
    return {"session": session_data(session), "messages": [
        {"id": str(m.id), "role": m.role, "content": m.content,
         "message_type": m.message_type, "message_metadata": m.message_metadata,
         "created_at": m.created_at} for m in messages]}


@router.delete("/session/{session_id}", status_code=204)
def delete_session(session_id: UUID, installation: AppInstallation = Depends(require_installation), db: Session = Depends(get_db)):
    session = get_owned_session(db, session_id, installation.id)
    if session is None:
        raise HTTPException(404, "채팅을 찾을 수 없습니다.")
    db.delete(session)
    db.commit()
    return Response(status_code=204)
