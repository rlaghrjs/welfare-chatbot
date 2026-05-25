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

## 3. 서버 실행

```bash
uvicorn app.main:app --reload
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
