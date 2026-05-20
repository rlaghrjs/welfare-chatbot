# FastAPI Welfare Project

복지 챗봇을 만들기위한 백엔드 FastAPi 입니다.

## 1. 가상환경 생성

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

macOS/Linux:

```bash
source .venv/bin/activate
```

## 2. 패키지 설치

```bash
pip install -r requirements.txt
```

## 3. 환경변수 설정

`.env.example` 파일을 복사해서 `.env` 파일을 만드세요.

```bash
copy .env.example .env
```

그리고 `.env` 안의 `WELFARE_API_KEY` 값을 본인 인증키로 바꾸세요.

## 4. PostgreSQL DB 생성

PostgreSQL에서 아래 DB를 생성하세요.

```sql
CREATE DATABASE welfare_app;
```

## 5. 서버 실행

```bash
uvicorn app.main:app --reload
```

## 6. API 확인

브라우저에서 접속:

```txt
http://127.0.0.1:8000/docs
```

## 주요 API

### 복지 데이터 가져와서 저장

```http
GET /api/welfare/fetch
```

### 저장된 복지 정책 목록 조회

```http
GET /api/welfare
```

### 특정 복지 정책 조회

```http
GET /api/welfare/{serv_id}
```

## 프로젝트 구조

```txt
app/
├── main.py
├── core/
│   └── config.py
├── db/
│   ├── database.py
│   └── init_db.py
├── models/
│   └── welfare_policy.py
├── schemas/
│   └── welfare_policy.py
├── routers/
│   └── welfare.py
└── services/
    └── welfare_service.py
```
