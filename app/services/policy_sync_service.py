"""Paginated list snapshots. No disappearance inference from incomplete responses."""
import hashlib
import json
from datetime import datetime, timezone
from sqlalchemy import func, text
from app.core.config import settings
from app.models.platform import SyncRun, WelfarePolicy, WelfarePolicyVersion
from app.services.welfare_api_common import fetch_xml, parse_xml, clean_text, WelfareAPIError
from app.services.welfare_service import build_welfare_params, parse_welfare_xml
from app.services.local_welfare_service import build_local_welfare_params, parse_local_welfare_xml
from app.services.notification_service import generate_notifications


def content_snapshot(policy):
    # Views and order are not policy changes. Keep untruncated descriptions.
    return {key: value for key, value in policy.items() if key not in {'inq_num', 'svcfrst_reg_ts'}}


def content_hash(policy):
    return hashlib.sha256(json.dumps(content_snapshot(policy), ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def store_policy(db, source, policy, run, baseline=False):
    policy = {**policy, '_source': source}
    digest = content_hash(policy)
    row = db.query(WelfarePolicy).filter_by(source=source, external_id=policy['serv_id']).with_for_update().first()
    now = datetime.now(timezone.utc)
    if row and row.content_hash == digest:
        row.last_seen_at = now
        return 'unchanged'
    previous = row.raw_data if row else {}
    change_type = 'updated' if row else 'new'
    if row is None:
        row = WelfarePolicy(source=source, external_id=policy['serv_id'], name=policy.get('serv_nm') or policy['serv_id'], content_hash=digest, raw_data=policy)
        db.add(row)
        db.flush()
    number = (db.query(func.max(WelfarePolicyVersion.version_no)).filter_by(policy_id=row.id).scalar() or 0) + 1
    row.name = policy.get('serv_nm') or policy['serv_id']
    row.summary = policy.get('serv_dgst')
    row.raw_data = policy
    row.content_hash = digest
    row.last_seen_at = now
    row.content_updated_at = now
    row.search_attributes = {'region': policy.get('ctpv_nm'), 'themes': policy.get('intrs_thema_array') or policy.get('intrs_thema_nm_array')}
    snapshot = content_snapshot(policy)
    changes = {k: {'before': previous.get(k), 'after': v} for k, v in snapshot.items() if previous.get(k) != v}
    version = WelfarePolicyVersion(policy_id=row.id, sync_run_id=run.id, version_no=number, change_type=change_type, snapshot=snapshot, changes=changes)
    db.add(version)
    db.flush()
    if not baseline:
        generate_notifications(db, version, policy)
    return change_type


async def collect(source, region=None):
    build, parse, url = (build_welfare_params, parse_welfare_xml, settings.welfare_api_url) if source == 'central' else (build_local_welfare_params, parse_local_welfare_xml, settings.local_welfare_api_url)
    params = build({'ctpvNm': region} if region else {})
    params['numOfRows'] = 1000
    rows = {}
    label = f"{source} / {region or '전체'}"
    print(f"[{label}] 수집 시작", flush=True)
    for page in range(1, 1001):
        params['pageNo'] = page
        print(f"[{label}] {page}페이지 요청 중...", flush=True)
        xml = await fetch_xml(url, params)
        print(f"[{label}] {page}페이지 응답 수신", flush=True)
        root = parse_xml(xml)
        code = root.findtext('.//resultCode')
        if code and code not in {'0', '00', '0000'}:
            raise WelfareAPIError('정책 수집 API가 실패 응답을 반환했습니다.')
        raw_items = root.findall('.//servList')
        policies = parse(xml)
        items_by_id = {item.findtext("servId", "").strip(): item for item in raw_items}
        for policy in policies:
            item = items_by_id[policy["serv_id"]]
            # Existing chat parsers truncate text; sync must preserve complete content.
            policy['serv_dgst'] = clean_text(item.findtext('servDgst'))
        fresh = [p for p in policies if p['serv_id'] not in rows]
        if policies and not fresh:
            raise WelfareAPIError('정책 수집 페이지가 반복되어 중단했습니다.')
        rows.update({p['serv_id']: p for p in fresh})
        total_text = root.findtext('.//totalCount')
        total = int(total_text) if total_text and total_text.isdigit() else None
        print(f"[{label}] {page}페이지 처리 완료 | 응답 {len(policies)}건 | 신규 수집 {len(fresh)}건 | 누적 {len(rows)}건 / 전체 {total if total is not None else '미확인'}건", flush=True)
        if not policies and total is None and page == 1:
            raise WelfareAPIError('정책 수집 응답에 목록과 전체 건수가 없습니다.')
        if not policies or (total is not None and len(rows) >= total):
            if total is not None and len(rows) < total:
                raise WelfareAPIError('정책 수집 결과가 전체 건수보다 적습니다.')
            print(f"[{label}] API 수집 완료: {len(rows)}건. DB 처리 단계로 이동합니다.", flush=True)
            return list(rows.values())
    raise WelfareAPIError('정책 수집 페이지 한도를 초과했습니다.')


async def sync_source(db, source, region=None):
    label = f"{source} / {region or '전체'}"
    scope_key = f"welfare-sync:{source}:{region or 'all'}"
    acquired = db.execute(
        text('SELECT pg_try_advisory_xact_lock(hashtext(:key))'),
        {'key': f'welfare-sync:{source}'},
    ).scalar()
    if not acquired:
        db.rollback()
        print(f"[{label}] 다른 수집기가 실행 중이어서 건너뜁니다.", flush=True)
        return {'source': source, 'status': 'skipped'}
    baseline = not db.query(SyncRun).filter_by(source=scope_key, status='success').first()
    run = SyncRun(source=scope_key, checkpoint={'baseline': baseline}, status='running')
    db.add(run)
    db.flush()
    try:
        print(f"[{label}] {'최초 기준 수집' if baseline else '신규·변경 확인'}", flush=True)
        policies = await collect(source, region)
        total = len(policies)
        print(f"[{label}] DB 처리 시작: 총 {total}건", flush=True)
        for index, policy in enumerate(policies, start=1):
            outcome = store_policy(db, source, policy, run, baseline)
            if outcome == 'new':
                run.created_count += 1
            elif outcome == 'updated':
                run.updated_count += 1
            if index % 100 == 0 or index == total:
                print(f"[{label}] DB 처리 {index}/{total}건 | 신규 {run.created_count}건 | 변경 {run.updated_count}건", flush=True)
        run.fetched_count = total
        run.status = 'success'
        run.finished_at = datetime.now(timezone.utc)
        created_count, updated_count = run.created_count, run.updated_count
        print(f"[{label}] DB 저장 확정 중...", flush=True)
        db.commit()
        print(f"[{label}] 저장 완료 | 수집 {total}건 | 신규 {created_count}건 | 변경 {updated_count}건", flush=True)
        if baseline:
            print(f"[{label}] 최초 기준 수집이므로 알림은 생성하지 않았습니다.", flush=True)
        return {'source': source, 'region': region, 'status': 'success', 'fetched': total,
                'created': created_count, 'updated': updated_count, 'baseline': baseline}
    except Exception as exc:
        db.rollback()
        print(f"[{label}] 동기화 실패: {type(exc).__name__}. 이번 범위의 DB 변경을 취소했습니다.", flush=True)
        db.add(SyncRun(source=scope_key, status='failed', failed_count=1,
                       error_summary=f"정책 동기화 실패: {type(exc).__name__}. API 설정과 연결을 확인해주세요.",
                       finished_at=datetime.now(timezone.utc)))
        db.commit()
        return {'source': source, 'region': region, 'status': 'failed'}
