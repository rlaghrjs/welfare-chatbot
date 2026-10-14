"""Installation IDs identify records; independent bearer secrets authorize access."""
import hashlib
import hmac
from datetime import datetime, timezone, timedelta
from uuid import UUID
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.platform import AppInstallation

bearer = HTTPBearer(auto_error=False)

def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()

def require_installation(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> AppInstallation:
    unauthorized = HTTPException(status_code=401, detail="앱 식별 정보를 확인해주세요.")
    if credentials is None:
        raise unauthorized
    try:
        installation_id, secret = credentials.credentials.split(".", 1)
        installation = db.get(AppInstallation, UUID(installation_id))
    except (ValueError, TypeError):
        raise unauthorized from None
    if not installation or not hmac.compare_digest(installation.token_hash, hash_token(secret)):
        raise unauthorized
    now = datetime.now(timezone.utc)
    last_seen = installation.last_seen_at
    if last_seen.tzinfo is None:
        last_seen = last_seen.replace(tzinfo=timezone.utc)
    if now - last_seen >= timedelta(hours=1):
        installation.last_seen_at = now
        db.commit()
    return installation
