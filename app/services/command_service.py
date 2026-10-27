# app/services/command_service.py

from datetime import datetime, timedelta
from sqlalchemy import func, desc
from app.db.database import SessionLocal
from app.models.search_log import SearchLog

def get_popular_keywords_response() -> str:
    """
    recent 30일간의 인기 관심주제 및 생애주기 키워드 Top 5를 집계하여
    챗봇 텍스트 메시지로 포맷팅하여 반환
    """
    db = SessionLocal()
    thirty_days_ago = datetime.now() - timedelta(days=30)

    try:
        # 최근 30일 관심주제 Top 5
        top_themes = (
            db.query(
                SearchLog.themekeyword.label("keyword"),
                func.count(SearchLog.id).label("count")
            )
            .filter(
                SearchLog.themekeyword.isnot(None),
                SearchLog.searched_at >= thirty_days_ago
            )
            .group_by(SearchLog.themekeyword)
            .order_by(desc("count"))
            .limit(5)
            .all()
        )

        # 최근 30일 생애주기 Top 5
        top_lifes = (
            db.query(
                SearchLog.lifekeyword.label("keyword"),
                func.count(SearchLog.id).label("count")
            )
            .filter(
                SearchLog.lifekeyword.isnot(None),
                SearchLog.searched_at >= thirty_days_ago
            )
            .group_by(SearchLog.lifekeyword)
            .order_by(desc("count"))
            .limit(5)
            .all()
        )

        # 메시지 구성
        response_text = "**최근 인기 복지 검색어 순위 (최근 30일)**\n\n"
        
        response_text += "**인기 관심 주제**\n"
        if top_themes:
            for idx, item in enumerate(top_themes, 1):
                response_text += f"{idx}. {item.keyword} ({item.count}회)\n"
        else:
            response_text += "집계된 데이터가 없습니다.\n"

        response_text += "\n**인기 대상/생애주기**\n"
        if top_lifes:
            for idx, item in enumerate(top_lifes, 1):
                response_text += f"{idx}. {item.keyword} ({item.count}회)\n"
        else:
            response_text += "집계된 데이터가 없습니다.\n"

        return response_text

    except Exception as e:
        print(f"[Command Service DB Error] 인기 검색어 집계 실패: {e}")
        return "인기 검색어를 불러오는 중 오류가 발생했습니다."
    finally:
        db.close()