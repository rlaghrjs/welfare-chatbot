import re
import html
import xml.etree.ElementTree as ET
import httpx

from sqlalchemy.orm import Session
from urllib.parse import urlencode
from app.core.config import settings
from app.models.welfare_policy import WelfarePolicy


def build_welfare_params(intent: dict) -> dict:
    params = {
        "serviceKey": settings.welfare_api_key,
        "callTp": "L",
        "pageNo": 1,
        "numOfRows": 10,
        "srchKeyCode": "001",
        "orderBy": "popular",
    }

    if intent.get("keyword"):
        params["searchWrd"] = intent["keyword"]

    if intent.get("lifeArray"):
        params["lifeArray"] = intent["lifeArray"]

    if intent.get("trgterIndvdlArray"):
        params["trgterIndvdlArray"] = intent["trgterIndvdlArray"]

    if intent.get("intrsThemaArray"):
        params["intrsThemaArray"] = intent["intrsThemaArray"]

    return params


def build_request_url(params: dict) -> str:
    return f"{settings.welfare_api_url}?{urlencode(params)}"


def get_text(element: ET.Element, tag_name: str) -> str | None:
    child = element.find(tag_name)
    if child is None or child.text is None:
        return None
    return child.text.strip()


def to_int(value: str | None) -> int | None:
    try:
        return int(value) if value else None
    except ValueError:
        return None


def parse_welfare_xml(xml_text: str) -> list[dict]:
    root = ET.fromstring(xml_text)
    serv_list = root.findall(".//servList")

    policies = []

    for item in serv_list:
        serv_id = get_text(item, "servId")

        if not serv_id:
            continue

        policies.append({
            "inq_num": to_int(get_text(item, "inqNum")),
            "intrs_thema_array": clean_text(get_text(item, "intrsThemaArray")),
            "jur_mnof_nm": clean_text(get_text(item, "jurMnofNm")),
            "jur_org_nm": clean_text(get_text(item, "jurOrgNm")),
            "life_array": clean_text(get_text(item, "lifeArray")),
            "onap_psblt_yn": clean_text(get_text(item, "onapPsbltYn")),
            "rprs_ctadr": clean_text(get_text(item, "rprsCtadr")),
            "serv_dgst": limit_text(get_text(item, "servDgst"), 1500),
            "serv_dtl_link": clean_text(get_text(item, "servDtlLink")),
            "serv_id": serv_id,
            "serv_nm": clean_text(get_text(item, "servNm")),
            "sprt_cyc_nm": clean_text(get_text(item, "sprtCycNm")),
            "srv_pvsn_nm": clean_text(get_text(item, "srvPvsnNm")),
            "svcfrst_reg_ts": clean_text(get_text(item, "svcfrstRegTs")),
            "trgter_indvdl_array": clean_text(get_text(item, "trgterIndvdlArray")),
        })

    return remove_duplicate_policies(policies)


async def fetch_save_and_return(db: Session, intent: dict) -> dict:
    params = build_welfare_params(intent)
    request_url = build_request_url(params)

    print("\n===== OPEN API REQUEST URL =====")
    print(request_url)
    print("================================\n")

    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.get(settings.welfare_api_url, params=params)
        response.raise_for_status()

    policies_data = parse_welfare_xml(response.text)

    saved_count = 0
    skipped_count = 0
    saved_or_existing_policies = []

    for data in policies_data:
        policy = (
            db.query(WelfarePolicy)
            .filter(WelfarePolicy.serv_id == data["serv_id"])
            .first()
        )

        if policy:
            skipped_count += 1
        else:
            policy = WelfarePolicy(**data)
            db.add(policy)
            db.flush()
            saved_count += 1

        saved_or_existing_policies.append(policy)

    db.commit()

    return {
        "request_url": request_url,
        "saved_count": saved_count,
        "skipped_count": skipped_count,
        "policies": saved_or_existing_policies,
    }


def clean_text(value: str | None) -> str | None:
    if value is None:
        return None

    value = html.unescape(value)
    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"\s+", " ", value)
    value = value.strip()

    if value in ["", "-", "null", "None", "정보 없음"]:
        return None

    return value


# 글자수 제한 함수
def limit_text(value: str | None, max_length: int = 1000) -> str | None:
    value = clean_text(value)

    if value is None:
        return None

    if len(value) > max_length:
        return value[:max_length] + "..."

    return value

# 중복 servId 제한 함수
def remove_duplicate_policies(policies: list[dict]) -> list[dict]:
    seen = set()
    result = []

    for policy in policies:
        serv_id = policy.get("serv_id")

        if not serv_id:
            continue

        if serv_id in seen:
            continue

        seen.add(serv_id)
        result.append(policy)

    return result