from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.welfare_api_result import WelfareApiResult


router = APIRouter(
    prefix="/api/welfare",
    tags=["Welfare"],
)


@router.get("/results")
def get_welfare_results(
    db: Session = Depends(get_db),
    session_id: UUID | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
):
    query = db.query(WelfareApiResult)

    if session_id:
        query = query.filter(WelfareApiResult.session_id == session_id)

    results = (
        query
        .order_by(WelfareApiResult.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return [
        {
            "id": str(item.id),
            "session_id": str(item.session_id),
            "query": item.query,
            "request_url": item.request_url,
            "intent": item.intent,
            "service_id": item.service_id,
            "service_name": item.service_name,
            "summary": item.summary,
            "raw_data": item.raw_data,
            "source": item.source,
            "created_at": item.created_at,
        }
        for item in results
    ]