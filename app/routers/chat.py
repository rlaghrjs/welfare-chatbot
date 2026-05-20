from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.chat import ChatRequest
from app.services.nlp_service import analyze_message
from app.services.welfare_service import fetch_save_and_return


router = APIRouter(
    prefix="/api/chat",
    tags=["Chat"],
)


@router.post("/search")
async def search_by_chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
):
    intent = analyze_message(request.message)

    result = await fetch_save_and_return(
        db=db,
        intent=intent,
    )

    return {
        "message": request.message,
        "intent": intent,
        "request_url": result["request_url"],
        "saved_count": result["saved_count"],
        "skipped_count": result["skipped_count"],
        "policies": [
            {
                "serv_id": p.serv_id,
                "serv_nm": p.serv_nm,
                "serv_dgst": p.serv_dgst,
                "serv_dtl_link": p.serv_dtl_link,
                "life_array": p.life_array,
                "intrs_thema_array": p.intrs_thema_array,
                "trgter_indvdl_array": p.trgter_indvdl_array,
            }
            for p in result["policies"]
        ],
    }