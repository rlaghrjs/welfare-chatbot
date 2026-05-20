def analyze_message(message: str) -> dict:
    text = message.strip()

    result = {
        "original_message": message,
        "keyword": text,

        "lifeArray": None,
        "lifeName": None,

        "trgterIndvdlArray": None,
        "trgterIndvdlName": None,

        "intrsThemaArray": None,
        "intrsThemaName": None,

        "servSeCode": None,
        "servSeName": None,
    }

    life_rules = {
        "001": ["영유아", "아기", "유아", "신생아"],
        "002": ["아동", "초등학생", "어린이"],
        "003": ["청소년", "중학생", "고등학생"],
        "004": ["청년", "대학생", "취준생", "취업준비생"],
        "005": ["중장년", "중년"],
        "006": ["노년", "노인", "어르신", "고령자"],
        "007": ["임신", "출산", "임산부", "산모"],
    }

    life_names = {
        "000": "구분없음(전생애)",
        "001": "영유아",
        "002": "아동",
        "003": "청소년",
        "004": "청년",
        "005": "중장년",
        "006": "노년",
        "007": "임신·출산",
    }

    target_rules = {
        "010": ["다문화", "탈북민", "북한이탈주민"],
        "020": ["다자녀"],
        "030": ["보훈", "국가유공자"],
        "040": ["장애", "장애인"],
        "050": ["저소득", "기초생활수급자", "차상위", "취약계층"],
        "060": ["한부모", "조손", "한부모가족"],
    }

    target_names = {
        "010": "다문화·탈북민",
        "020": "다자녀",
        "030": "보훈대상자",
        "040": "장애인",
        "050": "저소득",
        "060": "한부모·조손",
    }

    theme_rules = {
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

    theme_names = {
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

    service_rules = {
        "010": ["문의", "질문", "상담"],
        "020": ["사이트", "홈페이지", "웹사이트"],
        "030": ["근거", "법령", "법"],
        "040": ["서식", "자료", "양식"],
        "050": ["faq", "자주묻는질문"],
        "060": ["민원", "고객"],
        "070": ["복지사업", "시설", "단체"],
    }

    service_names = {
        "010": "문의",
        "020": "사이트",
        "030": "근거법령",
        "040": "서식/자료",
        "050": "관련 FAQ",
        "060": "민원고객",
        "070": "복지사업전담체계",
    }

    for code, words in life_rules.items():
        if any(word in text for word in words):
            result["lifeArray"] = code
            result["lifeName"] = life_names[code]
            break

    for code, words in target_rules.items():
        if any(word in text for word in words):
            result["trgterIndvdlArray"] = code
            result["trgterIndvdlName"] = target_names[code]
            break

    for code, words in theme_rules.items():
        if any(word in text for word in words):
            result["intrsThemaArray"] = code
            result["intrsThemaName"] = theme_names[code]
            break

    for code, words in service_rules.items():
        if any(word in text.lower() for word in words):
            result["servSeCode"] = code
            result["servSeName"] = service_names[code]
            break

    return result