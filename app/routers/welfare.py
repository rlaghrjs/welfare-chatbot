from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.welfare_policy import WelfarePolicy
from app.schemas.welfare_policy import FetchWelfareResponse, WelfarePolicyResponse
#from app.services.welfare_service import fetch_and_save_open_api_data


router = APIRouter(
    prefix="/api/welfare",
    tags=["Welfare"],
)


@router.get("/fetch", response_model=FetchWelfareResponse)
async def fetch_welfare_data(
    db: Session = Depends(get_db),
    call_tp: str = Query(default="L"),
    page_no: int = Query(default=1, ge=1),
    num_of_rows: int = Query(default=10, ge=1, le=500),
    srch_key_code: str = Query(default="001"),
    search_word: str | None = Query(default=None),
    life_array: str = Query(default="007"),
    trgter_indvdl_array: str = Query(default="050"),
    intrs_thema_array: str = Query(default="010"),
    age: int = Query(default=20, ge=0),
    onap_psblt_yn: str = Query(default="Y"),
    order_by: str = Query(default="popular"),
):
    result = await fetch_and_save_open_api_data(
        db=db,
        call_tp=call_tp,
        page_no=page_no,
        num_of_rows=num_of_rows,
        srch_key_code=srch_key_code,
        search_word=search_word,
        life_array=life_array,
        trgter_indvdl_array=trgter_indvdl_array,
        intrs_thema_array=intrs_thema_array,
        age=age,
        onap_psblt_yn=onap_psblt_yn,
        order_by=order_by,
    )

    return FetchWelfareResponse(
        message="OpenAPI 데이터 저장 완료",
        saved_count=result["saved_count"],
        skipped_count=result["skipped_count"],
    )


@router.get("", response_model=list[WelfarePolicyResponse])
def get_welfare_policies(
    db: Session = Depends(get_db),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
):
    return (
        db.query(WelfarePolicy)
        .order_by(WelfarePolicy.id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get("/{serv_id}", response_model=WelfarePolicyResponse)
def get_welfare_policy(
    serv_id: str,
    db: Session = Depends(get_db),
):
    policy = (
        db.query(WelfarePolicy)
        .filter(WelfarePolicy.serv_id == serv_id)
        .first()
    )

    if policy is None:
        raise HTTPException(status_code=404, detail="복지 정책을 찾을 수 없습니다.")

    return policy
