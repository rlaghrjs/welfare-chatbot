# 검색 로그 테이블 추가

이번 변경은 DB 모델과 마이그레이션만 제공합니다. 검색 키워드 추출·저장 연결,
순위 집계 API 및 화면은 포함하지 않습니다. 검색해도 이 테이블에 자동 저장되지 않습니다.

원본 SQL의 테이블명, 컬럼명, VARCHAR 길이 및 인덱스명을 유지합니다.
PostgreSQL에 맞춰 AUTO_INCREMENT는 IDENTITY, DATETIME은 TIMESTAMPTZ로 바꿉니다.

| 컬럼 | PostgreSQL 타입 | 설명 |
|---|---|---|
| id | BIGINT GENERATED ALWAYS AS IDENTITY | 독립 PK |
| lifekeyword | VARCHAR(100) | 생애주기 키워드, NULL 허용 |
| targetkeyword | VARCHAR(100) | 대상 특성 키워드, NULL 허용 |
| themekeyword | VARCHAR(100) | 관심 주제 키워드, NULL 허용 |
| age | INTEGER | 나이, NULL 허용 |
| searched_at | TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP | 검색 시각, NULL 허용 |

- `idx_searched_at`: searched_at
- `idx_keywords`: lifekeyword, targetkeyword, themekeyword 순서의 복합 인덱스
- 다른 테이블과의 외래키 관계 없음

프로젝트 가상환경에서 다음 명령을 실행하면 `0003_search_logs`가 적용됩니다.

```powershell
python -m alembic upgrade head
```

기존 0001/0002 마이그레이션은 수정하지 않습니다. 모델은
`app/models/search_log.py`, 생성 명세는 `migrations/versions/0003_search_logs.py`에 있습니다.
서버의 DB 버전 검사가 최신 마이그레이션을 요구하므로 서버 재시작 전에 적용합니다.
