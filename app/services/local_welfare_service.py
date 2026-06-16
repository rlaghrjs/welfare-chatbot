import html
import re
import xml.etree.ElementTree as ET
from urllib.parse import urlencode

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.welfare_api_result import WelfareApiResult


def build_local_welfare_params(intent: dict) -> dict:
    params = {
        "serviceKey": settings.local_welfare_api_key,
        "pageNo": 1,
        "numOfRows": 10,
        "srchKeyCode": "003",
        "arrgOrd": "inqNum",
    }

    if intent.get("searchWrd"):
        params["searchWrd"] = intent["searchWrd"]

    if intent.get("lifeArray"):
        params["lifeArray"] = intent["lifeArray"]

    if intent.get("trgterIndvdlArray"):
        params["trgterIndvdlArray"] = intent["trgterIndvdlArray"]

    if intent.get("intrsThemaArray"):
        params["intrsThemaArray"] = intent["intrsThemaArray"]

    if intent.get("age"):
        params["age"] = intent["age"]

    if intent.get("ctpvNm"):
        params["ctpvNm"] = intent["ctpvNm"]

    """
    if intent.get("sggNm"):
        params["sggNm"] = intent["sggNm"]

    """

    return params


def build_local_request_url(params: dict) -> str:
    return f"{settings.local_welfare_api_url}?{urlencode(params)}"


async def fetch_local_save_and_return(
    db: Session,
    session_id,
    query: str,
    intent: dict,
) -> dict:
    params = build_local_welfare_params(intent)
    request_url = build_local_request_url(params)

    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.get(
            settings.local_welfare_api_url,
            params=params,
        )
        response.raise_for_status()

    policies_data = parse_local_welfare_xml(response.text)

    saved_results = save_local_welfare_api_results(
        db=db,
        session_id=session_id,
        query=query,
        request_url=request_url,
        intent=intent,
        policies=policies_data,
    )

    return {
        "request_url": request_url,
        "saved_count": len(saved_results),
        "policies": policies_data,
    }


def parse_local_welfare_xml(xml_text: str) -> list[dict]:
    root = ET.fromstring(xml_text)
    serv_list = root.findall(".//servList")

    policies = []

    for item in serv_list:
        serv_id = get_text(item, "servId")

        if not serv_id:
            continue

        policies.append({
            "inq_num": to_int(get_text(item, "inqNum")),
            "serv_id": serv_id,
            "serv_nm": clean_text(get_text(item, "servNm")),
            "serv_dgst": limit_text(get_text(item, "servDgst"), 1500),
            "serv_dtl_link": clean_text(get_text(item, "servDtlLink")),

            "ctpv_nm": clean_text(get_text(item, "ctpvNm")),
            "sgg_nm": clean_text(get_text(item, "sggNm")),
            "biz_chr_dept_nm": clean_text(get_text(item, "bizChrDeptNm")),

            "aply_mtd_nm": clean_text(get_text(item, "aplyMtdNm")),
            "intrs_thema_nm_array": clean_text(get_text(item, "intrsThemaNmArray")),
            "last_mod_ymd": clean_text(get_text(item, "lastModYmd")),

            "sprt_cyc_nm": clean_text(get_text(item, "sprtCycNm")),
            "srv_pvsn_nm": clean_text(get_text(item, "srvPvsnNm")),

            "source_type": "local_welfare",
        })

    return remove_duplicate_policies(policies)


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


def limit_text(value: str | None, max_length: int = 1000) -> str | None:
    value = clean_text(value)

    if value is None:
        return None

    if len(value) > max_length:
        return value[:max_length] + "..."

    return value


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


def save_local_welfare_api_results(
    db: Session,
    session_id,
    query: str,
    request_url: str,
    intent: dict,
    policies: list[dict],
) -> list[WelfareApiResult]:
    saved_results = []

    for policy in policies:
        result = WelfareApiResult(
            session_id=session_id,
            query=query,
            request_url=request_url,
            intent=intent,
            service_id=policy.get("serv_id"),
            service_name=policy.get("serv_nm"),
            summary=policy.get("serv_dgst"),
            raw_data=policy,
            source="local_welfare",
        )

        db.add(result)
        saved_results.append(result)

    db.commit()

    for result in saved_results:
        db.refresh(result)

    return saved_results