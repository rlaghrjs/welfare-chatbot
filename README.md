# 복지정책 안내 챗봇

자연어 질문을 복지 OpenAPI 검색 조건으로 변환해 중앙정부·지방자치단체의 복지정책을 안내하는 웹 애플리케이션입니다. 익명 사용자별 대화 기록을 보관하고, 별도 수집기로 정책의 신규 등록과 내용 변경을 감지해 관심 조건에 맞는 앱 내부 알림을 제공합니다.

> 문서 기준: 2026-10-02, `develop` 기반 코드에 정책 수집·알림 기능을 추가한 버전입니다. 수집 페이지 크기를 1000으로 변경하고 `collect()`·`sync_source()`의 진행 로그를 추가한 운영 설정을 설명합니다. 기존 저장소 또는 최초 알림 ZIP만 받은 경우 해당 수집기 수정이 별도로 필요할 수 있습니다.

## 1. 주요 기능

| 기능 | 설명 |
|---|---|
| 자연어 복지 검색 | 질문에서 검색어·생애주기·가구 특성·관심 분야·나이를 추출하고 API 조건으로 매핑 |
| AI 분석 및 규칙 기반 대체 | `gpt-4o-mini`로 키워드 추출을 시도하고 실패하면 규칙 기반 분석 수행 |
| 중앙·지자체 결과 표시 | 두 API의 검색 결과를 출처별 카드로 표시 |
| 일반·프로필 맞춤 검색 | 질문 조건을 우선 적용하고, 맞춤 검색에서는 비어 있는 조건을 프로필 설정으로 보완 |
| 대화 기록 관리 | 첫 메시지에서 채팅방 생성, 목록 조회, 이전 메시지·결과 카드 복원, 채팅 삭제 |
| 익명 사용자 구분 | 브라우저에 저장한 설치 UUID와 비밀값으로 본인 데이터 접근 |
| 음성 입력 | 녹음 파일을 백엔드로 업로드해 한국어 텍스트로 변환 |
| 관심 조건 구독 | 지역·관심 분야·나이·키워드 조건과 알림 이벤트 설정 저장 |
| 정책 수집 및 버전 관리 | 목록 API를 페이지별로 수집하고 정책 ID·내용 해시를 비교해 변경 이력 저장 |
| 앱 내부 알림 | 구독에 맞는 신규·변경 정책 알림 조회, 읽지 않은 건수 표시, 읽음 처리 |
| 화면 설정 및 데이터 삭제 | 다크 모드·글자 크기·굵기 조절, 현재 설치의 사용자 데이터 삭제 |

알림은 정책 탐색을 돕는 정보입니다. 지원 대상 해당 여부나 신청 가능 여부를 확정하지 않으며, 실제 자격은 정책 상세 안내에서 확인해야 합니다.

## 2. 기술 구성

| 영역 | 구성 |
|---|---|
| 프론트엔드 | React, JavaScript/TypeScript, Vite, Tailwind CSS 3 |
| 백엔드 | Python, FastAPI, Uvicorn |
| DB 접근 | SQLAlchemy, PostgreSQL 드라이버 |
| 데이터베이스 | PostgreSQL; 현재 실행 환경에서는 Supabase 사용 |
| 스키마 관리 | Alembic 마이그레이션 |
| 외부 API 통신 | httpx, XML 응답 파싱 |
| 키워드 추출 | OpenAI API, 규칙 기반 키워드 매핑 |
| 음성 인식 | OpenAI `gpt-4o-mini-transcribe` |
| 변경 감지 | 정규화된 정책 JSON의 SHA-256 해시 비교 |

### 실시간 검색과 정책 수집의 구분

**채팅 검색**은 사용자의 질문 조건으로 외부 API를 직접 호출합니다. 결과 카드는 `chat_messages.message_metadata`에 당시 화면의 스냅샷으로 저장합니다. 현재 채팅 검색은 수집된 `welfare_policies`를 검색하는 방식이 아닙니다.

**정책 수집기**는 사용자 질문과 관계없이 중앙 정책 전체 및 지정 지역의 지자체 정책 목록을 수집합니다. 기존 정책과 비교한 뒤 버전과 알림을 생성합니다. 수집기를 실행하지 않아도 채팅 검색은 가능하지만 정책 변경 감지와 새 알림 생성은 진행되지 않습니다.

```mermaid
flowchart TD
    A["React 웹 앱"] --> B["FastAPI"]
    B --> C["중앙·지자체 복지 API"]
    B --> D["PostgreSQL"]
    E["별도 정책 수집기"] --> C
    E --> F["변경 감지·구독 매칭"]
    F --> D
```
<!--
## 3. 실행 준비

- Python: 코드 문법상 3.10 이상이 필요하며, 개발 검증에는 Python 3.12를 사용했습니다. 설치한 라이브러리의 Python 지원 범위도 확인합니다.
- Node.js 및 npm: `frontend/package-lock.json`의 엔진 조건을 충족해야 합니다. 현재 잠금 파일 기준으로 Node.js 20.19 이상인 20.x, 22.13 이상인 22.x, 또는 24 이상을 사용할 수 있습니다.
- 접속 가능한 PostgreSQL 데이터베이스
- 중앙·지자체 복지 OpenAPI의 호출 URL 및 인증키
- 키워드 추출·음성 인식을 위한 OpenAI API 키

아래 백엔드·수집기 명령은 `app/`, `scripts/`, `alembic.ini`가 있는 **프로젝트 루트**에서 실행합니다.

### 3.1 가상환경과 의존성

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Windows 명령 프롬프트에서는 `.venv\Scripts\activate.bat`로 활성화합니다.

macOS/Linux:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

### 3.2 백엔드 환경변수

프로젝트 루트에 `.env`를 생성합니다. 아래의 `YOUR_...` 값은 실제 발급 정보와 연결 정보로 교체해야 하는 자리표시자입니다.

```dotenv
APP_NAME=fastapi-welfare-chatbot
DATABASE_URL=postgresql+psycopg://YOUR_USER:YOUR_PASSWORD@YOUR_HOST:5432/YOUR_DATABASE?sslmode=require
WELFARE_API_URL=https://YOUR_CENTRAL_API_HOST/YOUR_LIST_ENDPOINT
WELFARE_API_KEY=YOUR_CENTRAL_SERVICE_KEY
LOCAL_WELFARE_API_URL=https://YOUR_LOCAL_API_HOST/YOUR_LIST_ENDPOINT
LOCAL_WELFARE_API_KEY=YOUR_LOCAL_SERVICE_KEY
OPENAI_API_KEY=YOUR_OPENAI_API_KEY
```

| 변수 | 용도 |
|---|---|
| `APP_NAME` | API 문서의 앱 이름; 생략 시 기본값 사용 |
| `DATABASE_URL` | 백엔드와 수집기가 함께 사용하는 PostgreSQL 연결 |
| `WELFARE_API_URL`, `WELFARE_API_KEY` | 중앙 복지 목록 API 주소와 인증키 |
| `LOCAL_WELFARE_API_URL`, `LOCAL_WELFARE_API_KEY` | 지자체 복지 목록 API 주소와 인증키 |
| `OPENAI_API_KEY` | 자연어 키워드 추출 및 음성 인식 |

`APP_NAME`을 제외한 위 설정은 현재 설정 클래스의 필수 항목입니다. AI 호출 실패 시 규칙 기반 대체가 있다고 해서 OpenAI 설정 없이 서버를 실행할 수 있는 것은 아닙니다.

Supabase에서는 접속 방식에 맞는 호스트·포트·사용자명·DB 이름을 사용합니다. 비밀번호에 URL 예약 문자가 포함되면 URL 인코딩이 필요합니다. `.env`, DB 비밀번호, API 키와 익명 사용자 비밀값은 저장소에 커밋하지 않습니다.

### 3.3 DB 마이그레이션

먼저 PostgreSQL 데이터베이스가 존재하고 연결 가능한 상태여야 합니다.

```powershell
python -m alembic upgrade head
```

이 명령은 해당 DB에 프로젝트 테이블과 스키마 변경을 적용합니다. PostgreSQL 서버나 데이터베이스 자체를 새로 만드는 명령은 아닙니다. 기존 DB를 변경하는 경우 백업과 현재 스키마를 확인합니다.

서버 시작 시 `init_db()`는 Alembic 버전이 최신인지 확인합니다. 서버 실행만으로 테이블 생성이나 마이그레이션이 자동 수행되지는 않습니다.
-->

## 4. 실행 방법

백엔드, 프론트엔드, 반복 수집기는 각각 별도 터미널에서 실행합니다.

### 터미널 1: 백엔드

프로젝트 루트에서 가상환경을 활성화하고 실행합니다.

```powershell
python -m uvicorn app.main:app --reload
```

- API: `http://127.0.0.1:8000`
- Swagger UI: `http://127.0.0.1:8000/docs`

현재 CORS 설정은 `http://localhost:5173`과 `http://127.0.0.1:5173`을 허용합니다. 다른 프론트 주소를 쓰면 `app/main.py`의 허용 출처도 수정해야 합니다.

### 터미널 2: 프론트엔드

```powershell
cd frontend
npm ci
npm run dev
```

브라우저에서 터미널에 표시된 Vite 주소로 접속합니다. 기본 주소는 `http://localhost:5173`입니다.

백엔드 주소를 변경하려면 `frontend/.env.example`을 참고해 `frontend/.env`를 만듭니다.

```dotenv
VITE_API_URL=http://127.0.0.1:8000
```

프론트 환경변수 변경 후에는 Vite를 재시작합니다. 서버용 API 키는 프론트 환경변수에 넣지 않습니다.

### 터미널 3: 정책 수집기

프로젝트 루트에서 백엔드와 동일한 가상환경·`.env`를 사용합니다.

**한 번 수집 후 종료:**

```powershell
python -m scripts.sync_policies --regions 서울특별시 인천광역시
```

**수집 완료 후 1시간 대기하며 반복:**

```powershell
python -m scripts.sync_policies --regions 서울특별시 인천광역시 --interval 3600
```

| 옵션 | 동작 |
|---|---|
| `--regions` | 지자체 수집 대상 시·도 이름; 생략 시 서울특별시 |
| `--interval` | 한 수집 주기를 마친 뒤 대기할 초; 생략하거나 0이면 한 번 실행 |

`--regions`는 지자체 API의 `ctpvNm`에만 적용됩니다. 중앙 정책은 지역 조건 없이 매 주기 한 차례 전체 페이지를 수집합니다. 지정한 지역을 순서대로 수집하며, 특정 범위가 실패해 실패 기록 저장까지 완료되면 다음 범위로 넘어갑니다.

서울·인천은 예시이며 전국 수집을 자동 의미하지 않습니다. 필요한 시·도를 지정해야 합니다. 해당 API가 인식하는 정확한 지역명을 사용합니다.

수집기는 FastAPI와 별도 DB 연결로 실행되므로 HTTP 서버 자체가 필수는 아니지만 DB와 환경 설정은 필요합니다. FastAPI만 실행하면 수집기는 자동으로 시작되지 않습니다. `Ctrl+C`로 수집기를 종료할 수 있습니다. 반복 수집 프로세스를 종료하면 새 정책 수집도 중단됩니다.

## 5. 수집 및 변경 감지

### 5.1 수집 조건

수집기는 검색어·나이·생애주기·관심 분야를 제한하지 않습니다. 중앙 목록 요청에는 `callTp=L`, `orderBy=popular`, 지자체 목록 요청에는 `ctpvNm`, `arrgOrd=inqNum`을 적용합니다. 두 요청 모두 `srchKeyCode=003`을 설정하지만 `searchWrd`는 보내지 않습니다.

운영 수정본의 `collect()`는 `numOfRows=1000`으로 요청하고 `pageNo`를 1부터 증가시킵니다. 실제 반환 건수는 API에 따라 달라질 수 있습니다. 누적 건수가 `totalCount`에 도달하거나 빈 페이지가 반환되면 수집을 종료하며, 전체 건수 미달·동일 페이지 반복·페이지 한도 초과를 오류로 처리합니다. 페이지 한도는 1000페이지입니다.

**페이지 크기 설정 위치:** `app/services/policy_sync_service.py`의 `collect()` 함수. 채팅 검색의 페이지 크기와는 별개입니다. 최초 배포본의 값은 100이므로 1000건 설정이 필요한 경우 이 함수를 확인합니다.

### 5.2 최초 수집과 재실행

| 상태 | 정책 저장 | 버전 저장 | 알림 |
|---|---|---|---|
| 해당 범위의 첫 성공 수집 | 기준 데이터 저장 | 최초 버전 저장 | 생성하지 않음 |
| 이후 처음 발견한 정책 | 새 정책 저장 | 새 버전 저장 | 구독 매칭 시 생성 |
| 이후 내용이 바뀐 정책 | 현재 정보 갱신 | 변경 버전 저장 | 구독 매칭 시 생성 |
| 내용이 동일한 정책 | 확인 시각 `last_seen_at` 갱신 | 추가 없음 | 추가 없음 |

정책 식별 기준은 `source + external_id`입니다. 최초 수집 여부는 중앙 또는 개별 지자체 지역의 `sync_runs` 성공 기록으로 판단합니다. 수집기를 껐다 켜도 같은 DB·같은 범위의 기록이 있으면 기존 기준을 이어 사용합니다. 새로운 지역을 처음 추가하면 그 지역의 첫 성공 수집은 알림 없는 기준 수집입니다.

매 실행마다 전체 API 목록을 가져오며 변경 없는 정책도 DB 조회와 확인 시각 갱신이 발생합니다. 최초 저장 이후에는 버전 생성 작업이 줄어들지만 DB 처리가 항상 즉시 끝나는 구조는 아닙니다. 현재 정책별 DB 접근의 일괄 처리 최적화는 적용하지 않았습니다.

### 5.3 내용 해시

`content_snapshot()`은 조회수 `inq_num`과 최초 등록 시각 `svcfrst_reg_ts`를 제외한 수집 필드를 사용합니다. JSON 키를 정렬하고 동일한 직렬화 형식으로 변환한 뒤 SHA-256 해시를 계산합니다.

- 정책명·요약·연락처·관심 분야·상세 링크 등 수집 항목의 변경은 해시에 반영됩니다.
- 지자체의 `last_mod_ymd`만 변경되어도 해시가 달라집니다.
- 조회수 또는 JSON 키의 나열 순서만 변경되면 해시는 유지됩니다.
- HTML 제거·공백 정리 등 파서의 텍스트 정규화 후 데이터를 비교합니다.
- 목록 API에 없는 상세 페이지 내용은 해시 비교 대상이 아닙니다.

따라서 현재 기준은 ‘제목과 본문만’이 아니라 **일부 변동성 항목을 제외한 수집 정보 전체**입니다.

### 5.4 트랜잭션과 진행 로그

각 수집 범위의 정책·버전·알림은 DB 트랜잭션 하나로 확정합니다. 처리 중 실패하면 해당 범위의 변경을 롤백하고 실패 이력을 남깁니다. 앞서 완료된 범위의 저장은 유지됩니다. 같은 소스의 동시 수집은 PostgreSQL advisory lock으로 방지합니다.

진행 로그 수정본은 페이지 요청·응답 수신·누적 수집 건수, DB 처리 100건마다의 진행 상황과 최종 저장 완료를 출력합니다. `DB 처리 100/…건`은 진행률이며, 저장 확정은 `저장 완료` 로그 이후입니다. 강제 중단된 범위는 저장이 확정되지 않을 수 있습니다. 최초 배포본에는 페이지별 진행 로그가 없을 수 있습니다.

## 6. 관심 조건과 앱 내부 알림

### 6.1 생성 과정

1. 사용자가 관심 조건을 저장합니다.
2. 수집기가 기준 수집 이후의 신규·변경 정책을 발견합니다.
3. 활성 구독 중 해당 이벤트를 받는 구독의 조건을 비교합니다.
4. 사용자·정책 버전·채널별로 알림을 생성합니다.
5. 수집 범위의 DB 커밋이 완료되면 웹에서 조회할 수 있습니다.
6. 앱 준비 완료 후 알림 API를 30초마다 조회하고 종 버튼에 읽지 않은 건수를 표시합니다.

같은 사용자의 여러 구독이 같은 정책 버전에 해당해도 알림은 하나입니다. 구독별 일치 근거는 `notification_matches`에 따로 저장합니다. 구독 등록 즉시 기존 정책 전체를 대상으로 과거 알림을 생성하지는 않습니다.

웹을 닫아도 수집기가 실행 중이면 알림을 저장할 수 있습니다. 브라우저가 닫힌 동안 팝업이 뜨는 푸시 방식은 아니며, 다시 접속해 저장된 알림을 확인합니다.

### 6.2 조건 예시

```json
{
  "name": "청년 주거 정책",
  "profile_id": null,
  "conditions": {
    "regions": ["서울특별시"],
    "themes": ["040"],
    "age": null,
    "include_keywords": ["월세", "임차료"],
    "exclude_keywords": []
  },
  "event_types": ["new", "updated"],
  "unknown_condition_policy": "include",
  "enabled": true
}
```

- 조건 항목 사이는 AND, 같은 목록 안은 OR이며 빈 목록은 제한 없음입니다.
- 포함·제외 키워드는 정책명과 요약에서 검사합니다. 제외 키워드가 있으면 매칭하지 않습니다.
- 현재 중앙 정책은 매칭 과정에서 전국 정책으로 취급합니다. 중앙 정책의 실제 지역 제한까지 검증하는 것은 아닙니다.
- 지자체 지역은 `ctpv_nm` 값과 비교합니다. 관심 분야는 API 코드·명칭을 비교하고 일부 지자체 명칭을 중앙 코드로 매핑합니다.
- 프로필을 연결하면 구독에서 지정하지 않은 지역·나이를 보완합니다. 생년월일의 만 나이는 한국 시간 기준으로 계산하며 직접 지정한 `age`는 자동 증가하지 않습니다.
- 현재 목록 데이터로 지원 연령을 검증하지 않으므로 나이는 미확인 조건으로 처리합니다. `include`이면 미확인 조건을 허용하고, `exclude`이면 제외합니다.
- 프론트 관심 조건 화면은 기본적으로 `new`, `updated`, 미확인 조건 `include`를 사용합니다. 프로필 연결·제외 키워드·추가 이벤트 설정 등 API가 지원하는 모든 입력이 화면에 노출되는 것은 아닙니다.
- `unavailable`, `restored`는 구독 요청 형식에 허용되지만 현재 수집기가 해당 이벤트를 생성하지 않습니다.

검색용 맞춤 프로필은 브라우저 설정이고, 알림 구독에서 참조하는 `profiles`는 서버 DB의 별도 자료입니다. 검색 설정 변경이 구독 조건에 자동 반영되는 구조는 아닙니다.

## 7. 데이터 저장 구조

모든 서버 데이터의 저장 위치는 `.env`의 `DATABASE_URL`입니다. 수집기를 재실행할 때마다 DB를 새로 생성하지 않습니다.

| 테이블 | 역할 |
|---|---|
| `app_installations` | 익명 설치 식별자와 비밀값 해시 |
| `chat_sessions` | 설치별 채팅방, 제목, 생성·수정 시간 |
| `chat_messages` | 질문·답변·검색 카드 스냅샷, 메시지 순번 |
| `profiles` | 구독에서 참조할 수 있는 서버 프로필 |
| `condition_subscriptions` | 사용자별 관심 조건과 활성 여부 |
| `welfare_policies` | 정책의 현재 정보, 해시, 최초·최근 확인 시각 |
| `welfare_policy_versions` | 정책별 버전, 스냅샷, 변경 항목 |
| `sync_runs` | 수집 범위와 성공·실패, 처리 건수 |
| `notifications` | 사용자별 앱 내부 알림과 읽음 상태 |
| `notification_matches` | 알림이 매칭된 구독과 조건 스냅샷 |
| `welfare_api_results` | 기존 API 검색 결과 보존용; 현재 채팅의 주 저장 경로는 아님 |
| `chat_search_results` | 메시지와 정책 버전 연결을 위한 테이블; 현재 채팅에서 사용하지 않음 |
| `policy_eligibility_rules` | 정책 버전별 자격 조건 저장용; 현재 수집기가 생성하지 않음 |

주요 관계는 설치 → 채팅방 → 메시지, 정책 → 정책 버전 → 알림, 알림 → 구독 일치 근거입니다. 채팅 메시지는 `sequence_no`로 순서를 복원합니다.

브라우저 `localStorage`에는 설치 ID·비밀값, 마지막 세션 ID와 화면·검색 설정을 저장합니다. 대화 본문과 정책 수집 데이터의 영구 저장소는 DB입니다. 브라우저 데이터를 지우면 기존 설치 인증 정보를 잃어 이전 기록에 접근하지 못할 수 있으며, 이것만으로 서버 데이터가 삭제되지는 않습니다.

## 8. 주요 API

| 메서드 | 경로 | 역할 |
|---|---|---|
| POST | `/api/installations` | 익명 설치 등록 |
| DELETE | `/api/installations/me` | 현재 설치의 채팅·프로필·구독·알림 삭제 |
| POST | `/api/chat/message` | 질문 처리, 첫 메시지에서 채팅방 생성 |
| GET | `/api/chat/sessions` | 본인 채팅 목록 |
| GET | `/api/chat/session/{session_id}` | 본인 채팅 상세와 메시지 |
| DELETE | `/api/chat/session/{session_id}` | 본인 채팅 삭제 |
| GET / POST | `/api/profiles` | 프로필 목록 / 생성 |
| PUT / DELETE | `/api/profiles/{profile_id}` | 프로필 수정 / 삭제 |
| GET / POST | `/api/subscriptions` | 구독 목록 / 생성 |
| PUT / DELETE | `/api/subscriptions/{subscription_id}` | 구독 수정 / 삭제 |
| GET | `/api/notifications?offset=0&limit=20` | 알림 목록, 전체·읽지 않은 건수 |
| PATCH | `/api/notifications/{notification_id}/read` | 본인 알림 읽음 처리 |
| POST | `/api/stt/transcribe` | `multipart/form-data`의 `file` 오디오를 텍스트로 변환 |

등록 외의 채팅·프로필·구독·알림·설치 삭제 API는 다음 인증 헤더를 사용합니다.

```http
Authorization: Bearer <installation_id>.<secret>
```

프론트는 공통 `apiFetch()`를 통해 인증 정보를 붙입니다. 현재 STT 라우터 자체에는 설치 인증 의존성이 없으므로 모든 API가 인증으로 보호된다고 해석하면 안 됩니다.

채팅 요청 예시:

```json
{
  "message": "청년 월세 지원 알려줘",
  "session_id": null,
  "ctpvNm": "서울특별시",
  "useProfile": true,
  "profile": {
    "age": 24,
    "lifeArray": "004",
    "trgterIndvdlArray": null,
    "intrsThemaArray": "040"
  }
}
```

새 대화는 `session_id`를 생략하거나 `null`로 보냅니다. 다음 질문에는 응답의 세션 ID를 사용합니다. 지역은 화면에서 선택해 보내는 것을 기본 사용 흐름으로 하며, 현재 백엔드 요청 스키마 자체가 지역 필수 입력을 강제하지는 않습니다.

## 9. 프로젝트 구조

| 경로 | 역할 |
|---|---|
| `app/main.py` | FastAPI 앱, 라우터, CORS, 시작 시 DB 버전 확인 |
| `app/core/` | 환경 설정과 외부 API 오류 처리 |
| `app/db/` | SQLAlchemy 엔진·세션·DB 상태 검사 |
| `app/models/` | 채팅·설치·정책·구독·알림 ORM 모델 |
| `app/schemas/` | 채팅·프로필·구독 요청 검증 |
| `app/routers/` | 채팅·설치·구독·알림·음성 인식 API |
| `app/services/nlp_service.py` | AI 키워드 추출과 규칙 기반 대체 |
| `app/services/welfare_service.py` | 중앙 검색 파라미터와 XML 파싱 |
| `app/services/local_welfare_service.py` | 지자체 검색 파라미터와 XML 파싱 |
| `app/services/welfare_api_common.py` | HTTP 요청, 정규화, API 키 마스킹 |
| `app/services/policy_sync_service.py` | 페이지 수집, 해시 비교, 버전 저장 |
| `app/services/notification_service.py` | 구독 매칭, 중복 방지, 알림 생성 |
| `scripts/sync_policies.py` | 단발·반복 수집 실행 진입점 |
| `migrations/` | Alembic 스키마 변경 |
| `frontend/src/api.ts`, `frontend/src/api/` | 익명 설치 인증과 API 호출 |
| `frontend/src/components/` | 채팅·설정·카드·알림 화면 |
| `frontend/src/SubscriptionsPanel.tsx` | 관심 조건 관리 화면 |
| `tests/`, `frontend/tests/` | 백엔드·프론트 동작 테스트 |
| `docs/`, `artifacts/` | DB·알림 보조 문서, ERD 자료 |

`app/routers/welfare.py`는 파일이 존재하지만 현재 `main.py`에서 등록하지 않습니다. 이 파일의 경로를 활성 API로 간주하지 않습니다. 기존 DB 전환 문서의 ‘수집·알림 미구현’ 설명은 전환 당시 상태이며, 이 README는 알림 추가 이후 기준입니다.

## 10. 테스트와 동작 확인

### 자동 검증

프로젝트 루트:

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```

프론트:

```powershell
cd frontend
npm test
npm run build
```

알림 기능 추가본에서 백엔드 테스트 26개와 프론트 테스트 11개, 프론트 빌드를 통과했습니다. 이 결과는 해당 검증 시점 기준이며 이후 수정의 통과를 보장하지 않습니다. 테스트는 주로 SQLite와 모의 API 응답을 사용하며 실제 복지 API·Supabase 연동 전체를 자동 검증한 결과는 아닙니다. 운영 환경의 단발 수집은 별도로 확인해야 합니다.

실제 PostgreSQL 마이그레이션 검증이 필요하면 프로젝트 루트에서 다음 스크립트를 실행할 수 있습니다.

```powershell
python tests/verify_postgres_migrations.py
```

이 스크립트는 설정된 PostgreSQL 안에 임시 스키마를 만들고 트랜잭션을 롤백합니다. `CREATE SCHEMA` 권한이 필요합니다.

### 수동 확인 순서

1. 마이그레이션 후 백엔드·프론트가 시작되는지 확인합니다.
2. 지역을 선택하고 복지 질문을 보내 중앙·지자체 카드가 표시되는지 확인합니다.
3. 새로고침 및 채팅 기록 선택으로 메시지·카드가 복원되는지 확인합니다.
4. 관심 조건을 등록하고 단발 수집을 실행합니다.
5. 수집 완료 로그와 `sync_runs.status`, `welfare_policies`·`welfare_policy_versions`를 확인합니다.
6. 같은 DB·같은 범위로 재실행해 기준 수집으로 돌아가지 않는지 확인합니다.
7. 이후 실제 신규·변경 정책이 조건과 매칭되면 알림 목록과 읽음 처리를 확인합니다.

첫 수집 직후 알림이 없거나 다음 수집에 변경 정책이 없으면 알림이 없는 것이 정상입니다. 알림 생성 로직 자체는 모의 데이터 테스트로 확인하고, 사용자 알림 DB를 임의 수정하는 방식은 피합니다.

## 11. 자주 확인할 문제

| 증상 | 확인할 사항 |
|---|---|
| 서버에서 DB 초기화·업데이트 필요 오류 | 올바른 `.env` 연결에서 `python -m alembic upgrade head` 실행 |
| `.env` 설정 검증 오류 | 실행 위치가 프로젝트 루트인지, 필수 변수가 있는지 확인 |
| Tailwind 모듈을 찾지 못함 | `frontend`에서 의존성 설치, Tailwind CSS 3 및 PostCSS 설정 확인 |
| 프론트 API 연결 실패 | 백엔드 주소, 실행 상태, CORS 허용 주소 확인 |
| 수집 중 출력이 없음 | 페이지 로그 수정본 적용 여부 확인; 최초 배포본은 주기 종료 후 결과 출력 |
| API 수집은 빠른데 DB 처리가 느림 | 정책별 조회·버전 저장과 원격 DB 왕복이 발생; 현재 일괄 처리 미적용 |
| `status=failed` | `sync_runs` 실패 기록, API 키·URL·XML 형식·DB 연결 확인 |
| 처음 수집했는데 알림 없음 | 기준 수집은 알림을 억제하므로 정상 |
| 이후 수집에도 알림 없음 | 신규·변경 여부, 구독 활성 상태·조건·이벤트·수집 지역 확인 |
| 기록이 사라진 것처럼 보임 | 브라우저 주소·프로필·저장된 설치 인증 정보 변경 여부 확인 |
| `psycopg2` 설치 시 `pg_config` 오류 | 해당 환경의 드라이버 빌드 준비 또는 바이너리 패키지 사용 검토; 프로젝트 요구사항과 일치시킬 것 |

## 12. 현재 제한 및 확장 과제

- 알림은 앱 내부 목록 조회 방식이며 브라우저 푸시·이메일·문자 발송은 구현하지 않았습니다.
- 상세 API 전체 수집은 구현하지 않았습니다. 목록에 없는 신청 기간·지원 조건 변경은 감지하지 못합니다.
- 종료·재개 이벤트는 생성하지 않으며 목록에서 사라졌다는 이유로 정책 종료를 판단하지 않습니다.
- 나이·소득·재산 등의 실제 지원 자격을 완전히 검증하지 않습니다.
- 중앙·지자체 채팅 검색은 순차 호출입니다. 한쪽 실패 시 다른 쪽 결과만 반환하는 부분 성공 처리는 적용하지 않았습니다.
- DB의 정책별 조회·저장, 신규·변경 정책별 구독 검사는 규모가 커지면 최적화가 필요합니다.
- 반복 수집은 실행 프로세스가 유지되는 동안만 동작합니다. 서버 재시작 후 자동 복구나 관리형 스케줄러는 별도 구성 사항입니다.
- 회원가입·계정 복구·여러 기기 간 기록 동기화는 제공하지 않습니다.

확장 시 우선 과제는 DB 일괄 처리, 상세 정보 수집과 변경 기준 개선, 지원 자격 검증, 수집 프로세스 운영 관리, 외부 푸시 채널 연동입니다.
