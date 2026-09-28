from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.platform import AppInstallation, Profile, ConditionSubscription
from app.schemas.subscriptions import ProfileRequest, SubscriptionRequest
from app.services.installation_service import require_installation

router = APIRouter(prefix="/api", tags=["Conditions and profiles"])


def owned(db, model, row_id, installation_id):
    row = db.query(model).filter(model.id == row_id, model.installation_id == installation_id).first()
    if row is None:
        raise HTTPException(404, "항목을 찾을 수 없습니다.")
    return row


def subscription_data(row):
    return {"id": str(row.id), "name": row.name,
            "profile_id": str(row.profile_id) if row.profile_id else None,
            "conditions": row.conditions, "event_types": row.event_types,
            "unknown_condition_policy": row.unknown_condition_policy, "enabled": row.enabled}


@router.get("/subscriptions")
def list_subscriptions(installation: AppInstallation = Depends(require_installation), db: Session = Depends(get_db)):
    return [subscription_data(row) for row in db.query(ConditionSubscription).filter_by(installation_id=installation.id).order_by(ConditionSubscription.created_at).all()]


def save_subscription(request, installation, db, row=None):
    if request.profile_id:
        owned(db, Profile, request.profile_id, installation.id)
    if row is None:
        row = ConditionSubscription(installation_id=installation.id)
        db.add(row)
    for key, value in request.model_dump().items():
        setattr(row, key, value)
    db.commit()
    return subscription_data(row)


@router.post("/subscriptions", status_code=201)
def create_subscription(request: SubscriptionRequest, installation: AppInstallation = Depends(require_installation), db: Session = Depends(get_db)):
    return save_subscription(request, installation, db)


@router.put("/subscriptions/{subscription_id}")
def update_subscription(subscription_id: UUID, request: SubscriptionRequest, installation: AppInstallation = Depends(require_installation), db: Session = Depends(get_db)):
    return save_subscription(request, installation, db, owned(db, ConditionSubscription, subscription_id, installation.id))


@router.delete("/subscriptions/{subscription_id}", status_code=204)
def delete_subscription(subscription_id: UUID, installation: AppInstallation = Depends(require_installation), db: Session = Depends(get_db)):
    db.delete(owned(db, ConditionSubscription, subscription_id, installation.id))
    db.commit()
    return Response(status_code=204)


def profile_data(row):
    return {"id": str(row.id), "name": row.name, "birth_date": row.birth_date, "region": row.region}


@router.get("/profiles")
def list_profiles(installation: AppInstallation = Depends(require_installation), db: Session = Depends(get_db)):
    return [profile_data(row) for row in db.query(Profile).filter_by(installation_id=installation.id).all()]


@router.post("/profiles", status_code=201)
def create_profile(request: ProfileRequest, installation: AppInstallation = Depends(require_installation), db: Session = Depends(get_db)):
    row = Profile(installation_id=installation.id, **request.model_dump())
    db.add(row)
    db.commit()
    return profile_data(row)


@router.put("/profiles/{profile_id}")
def update_profile(profile_id: UUID, request: ProfileRequest, installation: AppInstallation = Depends(require_installation), db: Session = Depends(get_db)):
    row = owned(db, Profile, profile_id, installation.id)
    for key, value in request.model_dump().items():
        setattr(row, key, value)
    db.commit()
    return profile_data(row)


@router.delete("/profiles/{profile_id}", status_code=204)
def delete_profile(profile_id: UUID, installation: AppInstallation = Depends(require_installation), db: Session = Depends(get_db)):
    row = owned(db, Profile, profile_id, installation.id)
    if db.query(ConditionSubscription).filter_by(profile_id=row.id).first():
        raise HTTPException(409, "이 프로필을 사용하는 구독을 먼저 변경하거나 삭제해주세요.")
    db.delete(row)
    db.commit()
    return Response(status_code=204)
