# 익명 설치·조건 구독 DB 전환

## 구현 범위

- 회원 계정 대신 설치 UUID와 별도의 256비트 이상 난수 비밀값을 사용합니다.
- 서버는 비밀값의 SHA-256 해시만 저장합니다. 설치 UUID만으로 조회할 수 없습니다.
- 첫 메시지의 저장과 채팅 생성은 하나의 트랜잭션입니다. 별도 생성/종료 API는 제거했습니다.
- 채팅별 순번으로 메시지 순서를 보장합니다. 삭제 시 메시지와 검색 결과 연결만 제거합니다.
- 설치별 조건 구독·프로필 CRUD와 전체 데이터 삭제 API를 제공합니다.
- 제도 원본, 버전, 대상 조건, 수집 기록, 알림, 일치 근거의 테이블과 제약을 준비했습니다.

**아직 구현하지 않은 부분:** 전체 OpenAPI 페이지/상세 수집, 변경 비교, 조건 매칭 실행,
주기 실행 작업, 앱 푸시 전송. 구독 화면에도 자동 수집·알림은 준비 중이라고 표시합니다.
현재 채팅은 기존처럼 실시간 API를 검색하고 표시한 카드를 메시지 메타데이터에 저장합니다.
수집기가 준비되면 `chat_search_results`의 제도 버전 참조로 전환합니다.

## ERD

- `artifacts/welfare_erd_v2.png`: 검은색 글씨 PNG
- `artifacts/welfare_erd_v2.mmd`: 수정 가능한 Mermaid 원본
- `app/models/platform.py`: 새 테이블 모델

## 적용

프로젝트 가상환경에서 다음을 실행합니다. 기존 DB는 사전에 백업해두세요.

```powershell
python -m pip install -r requirements.txt
python -m alembic upgrade head
python -m uvicorn app.main:app --reload
```

`0001_legacy`는 원래 세 테이블을 채택하고, `0002_anonymous_conditions`는 새 테이블과
채팅 소유권·순번을 추가합니다. 빈 DB도 같은 명령으로 초기화합니다.
이 절차는 저장소의 원래 스키마를 기준으로 하며 별도로 변경한 DB는 먼저 비교해야 합니다.
앱 시작 시 스키마 버전을 확인하며, 서버가 임의로 마이그레이션을 실행하지 않습니다.
자동 다운그레이드는 데이터 손실 방지를 위해 제공하지 않습니다. 필요 시 검토한 백업으로 복구합니다.

### 과거 기록 보존

- 기존 채팅의 소유자를 알 수 없으므로 `installation_id=NULL`로 보존합니다.
  어떤 새 설치에도 자동 귀속하지 않으며 일반 API에는 노출하지 않습니다.
- `status`, `ended_at`는 `legacy_status`, `legacy_ended_at`로 이름을 바꿔 보존합니다.
  새 코드에서는 사용하지 않습니다. 추후 별도 정리 마이그레이션으로 제거할 수 있습니다.
- `welfare_api_results`는 과거 검색 응답 보존용으로 남습니다. 새 채팅은 이 테이블에 쓰지 않습니다.
- 기존 메시지는 생성 시각·ID 순으로 순번을 부여합니다. 과거 동일 시각 메시지의 실제 순서는
  기록만으로 복원할 수 없습니다. 새 메시지는 채팅 행 잠금과 순번 고유 제약으로 순서를 보장합니다.

## API

| 메서드/경로 | 역할 |
|---|---|
| POST `/api/installations` | `{installation_id, secret}`로 익명 등록. 같은 비밀값으로 재시도 가능 |
| DELETE `/api/installations/me` | 현재 설치의 채팅·프로필·구독·알림 삭제 |
| POST `/api/chat/message` | `{message, session_id?: UUID}`. ID가 없으면 첫 메시지에서 생성 |
| GET `/api/chat/sessions` | 현재 설치의 채팅 목록 |
| GET, DELETE `/api/chat/session/{id}` | 본인 채팅 조회·삭제 |
| GET, POST `/api/subscriptions` | 조건 구독 목록·생성 |
| PUT, DELETE `/api/subscriptions/{id}` | 조건 구독 교체·삭제 |
| GET, POST `/api/profiles` | 선택 프로필 목록·생성 |
| PUT, DELETE `/api/profiles/{id}` | 선택 프로필 수정·삭제 |

등록 외 API는 `Authorization: Bearer <installation_id>.<secret>`를 사용합니다.
프로필을 참조하는 구독이 있으면 프로필 삭제는 거부합니다. 먼저 구독을 변경/삭제해야 합니다.
채팅 삭제는 구독·제도·변경 이력을 지우지 않습니다. 구독 삭제도 기존 알림과 일치 근거를 보존합니다.

## 조건 형식

```json
{
  "name": "내 주거 지원",
  "profile_id": null,
  "conditions": {
    "regions": ["서울특별시"],
    "themes": ["040"],
    "age": 27,
    "include_keywords": [],
    "exclude_keywords": []
  },
  "event_types": ["new", "updated"],
  "unknown_condition_policy": "include",
  "enabled": true
}
```

필드 사이는 AND, 같은 목록 안은 OR입니다. 빈 목록은 제한 없음입니다.
명시한 구독 값이 프로필보다 우선하며, 프로필 참조 시 생년월일로 실행 시점의 만 나이를 계산하는
매칭 로직을 후속 단계에서 구현합니다. 고정 `age` 조건은 자동 증가하지 않습니다.
소득·재산 등 아직 지원하지 않는 조건 키는 거부합니다.
전국 제도 포함, 모호한 조건의 처리, 최초 수집 알림 억제는 수집·매칭 단계에서 검증해야 합니다.

## 설치 식별 저장

현재 프로젝트는 웹 앱이므로 `localStorage`에 설치 ID/비밀값을 저장합니다.
이는 앱 삭제까지 유지되는 네이티브 설치 저장소와 같지 않습니다. 브라우저 데이터 삭제·시크릿 모드·
다른 브라우저/주소에서는 새 설치가 됩니다. 실제 모바일 앱에서는 보안 저장소와 백업 제외 정책을
적용해야 합니다. 배포 시 HTTPS가 필요하며 토큰을 URL이나 로그에 넣지 않습니다.
앱 삭제를 서버에서 즉시 감지할 수 없으므로 미접속 데이터 보관 기간은 별도 정책으로 정해야 합니다.

## 검증

```powershell
python -m unittest discover -s tests -v
python tests/verify_postgres_migrations.py
cd frontend
npm run build
npm run lint
```

단위/통합 테스트는 메모리 SQLite와 가짜 API 응답을 사용합니다.
PostgreSQL 검증 스크립트는 `.env` DB에 고유한 임시 스키마를 생성해 마이그레이션을 실행하고
전체 트랜잭션을 롤백합니다. 기존 테이블은 변경하지 않으며 `CREATE SCHEMA` 권한이 필요합니다.
