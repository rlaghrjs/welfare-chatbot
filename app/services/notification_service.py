"""Condition matching for discovery alerts, not eligibility guarantees."""
import re
from datetime import datetime, timezone
from app.models.platform import ConditionSubscription, Profile, Notification, NotificationMatch


def terms(value):
    return {x.strip().casefold() for x in re.split(r'[,|;/]', value or '') if x.strip()}


THEME_CODES = {'신체건강': '010', '정신건강': '020', '생활지원': '030', '주거': '040', '일자리': '050', '문화·여가': '060', '안전·위기': '070', '임신·출산': '080', '보육': '090', '교육': '100', '입양·위탁': '110', '보호·돌봄': '120', '서민금융': '130', '법률': '140'}


def theme_terms(policy):
    actual = terms(policy.get('intrs_thema_array')) | terms(policy.get('intrs_thema_nm_array'))
    return actual | {THEME_CODES[t] for t in actual if t in THEME_CODES}


def match_conditions(conditions, policy, unknown='include'):
    text = ' '.join(str(policy.get(k) or '') for k in ('serv_nm', 'serv_dgst')).casefold()
    if any(word.casefold() in text for word in conditions.get('exclude_keywords', [])):
        return False
    included = conditions.get('include_keywords', [])
    if included and not any(word.casefold() in text for word in included):
        return False
    for field, actual in (
        ('regions', {'전국'} if policy.get('_source') == 'central' else terms(policy.get('ctpv_nm'))),
        ('themes', theme_terms(policy)),
    ):
        wanted = {v.casefold() for v in conditions.get(field, [])}
        if wanted and actual and '전국' not in actual and not wanted & actual:
            return False
        if wanted and not actual and unknown == 'exclude':
            return False
    # The list API does not supply verified age eligibility.
    if conditions.get('age') is not None and unknown == 'exclude':
        return False
    return True


def effective_conditions(subscription, profile=None):
    conditions = dict(subscription.conditions)
    if profile:
        if not conditions.get('regions') and profile.region:
            conditions['regions'] = [profile.region]
        if conditions.get('age') is None and profile.birth_date:
            from zoneinfo import ZoneInfo
            today = datetime.now(ZoneInfo('Asia/Seoul')).date()
            birth = profile.birth_date
            conditions['age'] = today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
    return conditions


def generate_notifications(db, version, policy):
    for subscription in db.query(ConditionSubscription).filter_by(enabled=True).all():
        if version.change_type not in subscription.event_types:
            continue
        profile = db.query(Profile).filter_by(id=subscription.profile_id, installation_id=subscription.installation_id).first() if subscription.profile_id else None
        conditions = effective_conditions(subscription, profile)
        if not match_conditions(conditions, policy, subscription.unknown_condition_policy):
            continue
        notification = db.query(Notification).filter_by(installation_id=subscription.installation_id, policy_version_id=version.id, channel='app').first()
        if notification is None:
            label = '신규 정책' if version.change_type == 'new' else '정책 변경'
            notification = Notification(installation_id=subscription.installation_id, policy_version_id=version.id, channel='app', title=f'{label}: {policy.get("serv_nm")}', body=policy.get('serv_dgst') or '정책 상세 정보를 확인해주세요.', delivery_status='sent', sent_at=datetime.now(timezone.utc))
            db.add(notification)
            db.flush()
        if not db.query(NotificationMatch).filter_by(notification_id=notification.id, subscription_id=subscription.id).first():
            db.add(NotificationMatch(notification_id=notification.id, subscription_id=subscription.id, conditions_snapshot=conditions, match_reason={'event': version.change_type, 'unknown_condition_policy': subscription.unknown_condition_policy, 'notice': '지원 자격 확정이 아닌 관심 조건 매칭입니다.'}))
            db.flush()
