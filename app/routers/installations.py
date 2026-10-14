import hmac
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, Field
from sqlalchemy import delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.platform import AppInstallation, ConditionSubscription, Profile
from app.services.installation_service import hash_token, require_installation

router = APIRouter(prefix="/api/installations", tags=["Anonymous installations"])

class InstallationRegistration(BaseModel):
    installation_id: UUID
    # Persisted before registering so retries cannot lose the credential.
    secret: str = Field(min_length=43, max_length=128, pattern=r"^[A-Za-z0-9_-]+$")

@router.post("", status_code=201)
def register(request: InstallationRegistration, db: Session = Depends(get_db)):
    token_hash = hash_token(request.secret)
    existing = db.get(AppInstallation, request.installation_id)
    if not existing:
        db.add(AppInstallation(id=request.installation_id, token_hash=token_hash))
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
        existing = db.get(AppInstallation, request.installation_id)
    if not existing or not hmac.compare_digest(existing.token_hash, token_hash):
        raise HTTPException(status_code=409, detail="다른 앱 식별 정보가 이미 등록되어 있습니다.")
    return {"installation_id": str(existing.id)}

@router.delete("/me", status_code=204)
def delete_installation(installation: AppInstallation = Depends(require_installation), db: Session = Depends(get_db)):
    db.execute(delete(ConditionSubscription).where(ConditionSubscription.installation_id == installation.id))
    db.execute(delete(Profile).where(Profile.installation_id == installation.id))
    db.delete(installation)
    db.commit()
    return Response(status_code=204)
