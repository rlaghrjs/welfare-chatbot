from datetime import datetime, timezone
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.platform import AppInstallation, Notification, WelfarePolicyVersion
from app.routers.subscriptions import owned
from app.services.installation_service import require_installation

router = APIRouter(prefix='/api/notifications', tags=['Notifications'])


@router.get('')
def list_notifications(offset: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100), installation: AppInstallation = Depends(require_installation), db: Session = Depends(get_db)):
    query = db.query(Notification).filter_by(installation_id=installation.id, channel='app')
    unread = query.filter(Notification.read_at.is_(None)).count()
    items = []
    for row in query.order_by(Notification.created_at.desc(), Notification.id.desc()).offset(offset).limit(limit).all():
        version = db.get(WelfarePolicyVersion, row.policy_version_id)
        items.append({'id': str(row.id), 'title': row.title, 'body': row.body, 'created_at': row.created_at, 'read_at': row.read_at, 'policy': version.snapshot, 'change_type': version.change_type})
    return {'items': items, 'unread_count': unread, 'total': query.count()}


@router.patch('/{notification_id}/read')
def read_notification(notification_id: UUID, installation: AppInstallation = Depends(require_installation), db: Session = Depends(get_db)):
    row = owned(db, Notification, notification_id, installation.id)
    if row.read_at is None:
        row.read_at = datetime.now(timezone.utc)
        db.commit()
    return {'id': str(row.id), 'read_at': row.read_at}
