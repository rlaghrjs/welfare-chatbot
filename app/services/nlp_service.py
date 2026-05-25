import os
from typing import Optional, Literal
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


LIFE_RULES = {
    "001": ["영유아", "아기", "유아", "신생아"],
    "002": ["아동", "초등학생", "어린이"],
    "003": ["청소년", "중학생", "고등학생"],
    "004": ["청년", "대학생", "취준생", "취업준비생"],
    "005": ["중장년", "중년"],
    "006": ["노년", "노인", "어르신", "고령자"],
    "007": ["임신", "출산", "임산부", "산모"],
}

LIFE_NAMES = {
    "000": "구분없음(전생애)",
    "001": "영유아",
    "002": "아동",
    "003": "청소년",
    "004": "청년",
    "005": "중장년",
    "006": "노년",
    "007": "임신·출산",
}

TARGET_RULES = {
    "010": ["다문화", "탈북민", "북한이탈주민"],
    "020": ["다자녀"],
    "030": ["보훈", "국가유공자"],
    "040": ["장애", "장애인"],
    "050": ["저소득", "기초생활수급자", "차상위", "취약계층"],
    "060": ["한부모", "조손", "한부모가족"],
}

TARGET_NAMES = {
    "010": "다문화·탈북민",
    "020": "다자녀",
    "030": "보훈대상자",
    "040": "장애인",
    "050": "저소득",
    "060": "한부모·조손",
}

THEME_RULES = {
    "010": ["신체건강", "건강", "병원", "의료", "진료", "치료"],
    "020": ["정신건강", "우울", "상담", "심리"],
    "030": ["생활지원", "생계", "생활비", "지원금"],
    "040": ["주거", "월세", "전세", "임대", "집", "주택"],
    "050": ["일자리", "취업", "구직", "고용", "실업"],
    "060": ["문화", "여가", "여행"],
    "070": ["안전", "위기", "긴급"],
    "080": ["임신", "출산", "임산부", "산모"],
    "090": ["보육", "육아", "아이돌봄", "돌봄"],
    "100": ["교육", "장학금", "학비", "학교"],
    "110": ["입양", "위탁"],
    "120": ["보호돌봄", "요양", "간병", "돌봄"],
    "130": ["서민금융", "대출", "금융", "이자"],
    "140": ["법률", "소송", "상담"],
    "150": ["관계개선", "가족관계", "갈등"],
    "160": ["에너지", "전기", "가스", "난방"],
}

THEME_NAMES = {
    "010": "신체건강",
    "020": "정신건강",
    "030": "생활지원",
    "040": "주거",
    "050": "일자리",
    "060": "문화·여가",
    "070": "안전·위기",
    "080": "임신·출산",
    "090": "보육",
    "100": "교육",
    "110": "입양·위탁",
    "120": "보호·돌봄",
    "130": "서민금융",
    "140": "법률",
    "150": "관계개선",
    "160": "에너지",
}


class ExtractedKeywords(BaseModel):
    searchWrd: Optional[str] = Field(
        default=None,
        description="등록금, 장학금, 월세, 전세, 기저귀, 수술비 같은 구체적인 핵심 명사. 복지/지원/제도/방법/알려줘 같은 포괄어는 제외."
    )
    lifeKeyword: Optional[str] = Field(default=None, description="생애주기 관련 키워드")
    targetKeyword: Optional[str] = Field(default=None, description="대상특성 관련 키워드")
    themeKeyword: Optional[str] = Field(default=None, description="관심주제 관련 키워드")
    age: Optional[int] = Field(default=None, description="나이가 있으면 숫자만")


def normalize_empty(value):
    if value is None:
        return None

    value = str(value).strip()

    if value.lower() in ["", "null", "none", "없음"]:
        return None

    return value


def match_code(keyword: Optional[str], rules: dict[str, list[str]]) -> Optional[str]:
    keyword = normalize_empty(keyword)

    if not keyword:
        return None

    for code, words in rules.items():
        if any(word in keyword for word in words):
            return code

    return None


def extract_keywords_by_ai(user_input: str) -> dict:
    system_prompt = """
    당신은 복지 검색 키워드 추출 AI입니다.

    사용자의 문장에서 아래 항목을 추출하세요.

    1. searchWrd:
    - 사용자가 찾고자 하는 구체적인 핵심 명사만 추출
    - 예: 월세, 전세, 등록금, 장학금, 병원비, 수술비, 생활비, 기저귀
    - '복지', '지원', '제도', '혜택', '방법', '알려줘'는 제외
    - 없으면 null

    2. lifeKeyword:
    - 영유아, 아동, 청소년, 청년, 중장년, 노년, 임신, 출산 중 관련 표현
    - 예: 대학생, 취준생은 청년
    - 없으면 null

    3. targetKeyword:
    - 다문화, 탈북민, 다자녀, 보훈, 장애인, 저소득, 한부모, 조손 중 관련 표현
    - 직접 언급이 없으면 null

    4. themeKeyword:
    - 신체건강, 정신건강, 생활지원, 주거, 일자리, 문화, 여가, 안전, 위기,
      임신, 출산, 보육, 교육, 입양, 위탁, 보호돌봄, 서민금융, 법률, 관계개선, 에너지 중 관련 표현
    - 월세/전세/집은 주거
    - 등록금/장학금/학비는 교육
    - 병원비/수술비는 신체건강
    - 생활비/생계비는 생활지원
    - 없으면 null

    5. age:
    - 25살, 만 19세처럼 나이가 있으면 숫자만
    - 없으면 null

    절대 OpenAPI 코드를 직접 만들지 마세요.
    코드는 서버에서 매핑합니다.
    """

    completion = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input},
        ],
        response_format=ExtractedKeywords,
    )

    return completion.choices[0].message.parsed.model_dump()


def analyze_message(user_input: str) -> dict:
    extracted = extract_keywords_by_ai(user_input)

    search_wrd = normalize_empty(extracted.get("searchWrd"))
    life_keyword = normalize_empty(extracted.get("lifeKeyword"))
    target_keyword = normalize_empty(extracted.get("targetKeyword"))
    theme_keyword = normalize_empty(extracted.get("themeKeyword"))

    life_code = match_code(life_keyword, LIFE_RULES)
    target_code = match_code(target_keyword, TARGET_RULES)
    theme_code = match_code(theme_keyword, THEME_RULES)

    return {
        "original_message": user_input,

        "searchWrd": search_wrd,

        "lifeKeyword": life_keyword,
        "lifeArray": life_code,
        "lifeName": LIFE_NAMES.get(life_code) if life_code else None,

        "targetKeyword": target_keyword,
        "trgterIndvdlArray": target_code,
        "trgterIndvdlName": TARGET_NAMES.get(target_code) if target_code else None,

        "themeKeyword": theme_keyword,
        "intrsThemaArray": theme_code,
        "intrsThemaName": THEME_NAMES.get(theme_code) if theme_code else None,

        "age": extracted.get("age"),
    }