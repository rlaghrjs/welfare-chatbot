from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.welfare_api_result import WelfareApiResult
from app.services.welfare_api_common import (
    build_safe_request_url, clean_text, fetch_xml, get_text, limit_text,
    parse_xml, remove_duplicate_policies, save_api_results, to_int,
)


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

    if intent.get("age") is not None and intent.get("age") != "":
        params["age"] = intent["age"]

    if intent.get("ctpvNm"):
        params["ctpvNm"] = intent["ctpvNm"]

    """
    if intent.get("sggNm"):
        params["sggNm"] = intent["sggNm"]

    """

    return params


def build_local_request_url(params: dict) -> str:
    return build_safe_request_url(settings.local_welfare_api_url, params)


async def fetch_local_save_and_return(
    db: Session,
    session_id,
    query: str,
    intent: dict,
) -> dict:
    params = build_local_welfare_params(intent)
    request_url = build_local_request_url(params)

    xml_text = await fetch_xml(settings.local_welfare_api_url, params)
    policies_data = parse_local_welfare_xml(xml_text)

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
    root = parse_xml(xml_text)
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


def save_local_welfare_api_results(
    db: Session,
    session_id,
    query: str,
    request_url: str,
    intent: dict,
    policies: list[dict],
) -> list[WelfareApiResult]:
    return save_api_results(
        db, session_id, query, request_url, intent, policies, source="local_welfare",
    )
