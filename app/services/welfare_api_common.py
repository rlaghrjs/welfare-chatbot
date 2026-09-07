"""Shared transport, normalization and persistence for welfare providers."""
import html
import re
import xml.etree.ElementTree as ET
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import httpx
from sqlalchemy.orm import Session
from app.models.welfare_api_result import WelfareApiResult


class WelfareAPIError(Exception):
    """An upstream failure with a safe, credential-free message."""


def redact_request_url(url: str) -> str:
    parts = urlsplit(url)
    query = [(key, '[REDACTED]' if key.lower() == 'servicekey' else value)
             for key, value in parse_qsl(parts.query, keep_blank_values=True)]
    return urlunsplit(parts._replace(query=urlencode(query)))


def build_safe_request_url(url: str, params: dict) -> str:
    parts = urlsplit(url)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    query.update(params)
    return redact_request_url(urlunsplit(parts._replace(query=urlencode(query))))


async def fetch_xml(url: str, params: dict) -> str:
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.text
    except httpx.HTTPError:
        raise WelfareAPIError('복지 API 요청에 실패했습니다. 잠시 후 다시 시도해주세요.') from None


def parse_xml(xml_text: str) -> ET.Element:
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        raise WelfareAPIError('복지 API 응답 형식이 올바르지 않습니다.') from None
    if root.tag == 'OpenAPI_ServiceResponse' or root.find('.//cmmMsgHeader/errMsg') is not None:
        raise WelfareAPIError('복지 API에서 오류 응답을 반환했습니다.')
    return root


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


def save_api_results(
    db: Session,
    session_id,
    query: str,
    request_url: str,
    intent: dict,
    policies: list[dict],
    source: str,
) -> list[WelfareApiResult]:
    saved_results = []

    for policy in policies:
        result = WelfareApiResult(
            session_id=session_id,
            query=query,
            request_url=redact_request_url(request_url),
            intent=intent,
            service_id=policy.get("serv_id"),
            service_name=policy.get("serv_nm"),
            summary=policy.get("serv_dgst"),
            raw_data=policy,
            source=source,
        )

        saved_results.append(result)

    try:
        db.add_all(saved_results)
        db.commit()
    except Exception:
        db.rollback()
        raise

    return saved_results