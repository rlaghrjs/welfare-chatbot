"""실제 중앙·지자체 복지 API 연결 확인: python check_welfare_api.py

프로젝트의 .env를 사용합니다. DB 저장이나 OpenAI 호출은 하지 않습니다.
"""

import asyncio
import os
from pathlib import Path


async def main() -> int:
    # 다른 폴더에서 실행해도 프로젝트의 .env를 읽습니다.
    os.chdir(Path(__file__).resolve().parent)
    try:
        from app.core.config import settings
        from app.services.welfare_api_common import WelfareAPIError, fetch_xml
        from app.services.welfare_service import build_welfare_params, parse_welfare_xml
        from app.services.local_welfare_service import (
            build_local_welfare_params, parse_local_welfare_xml,
        )
    except Exception as exc:
        # 설정 검증 오류에는 인증키가 포함될 수 있어 원문은 출력하지 않습니다.
        print(f"[실패] 설정/라이브러리 로드 오류 ({type(exc).__name__}).")
        print("requirements.txt 설치와 .env의 필수 설정을 확인해주세요.")
        return 1

    providers = [
        ("중앙", settings.welfare_api_url, build_welfare_params, parse_welfare_xml),
        ("지자체", settings.local_welfare_api_url,
         build_local_welfare_params, parse_local_welfare_xml),
    ]
    failures = 0
    for name, url, build_params, parse in providers:
        print(f"[{name}] 실제 API 조회 중...", flush=True)
        params = build_params({})
        params["numOfRows"] = 3
        try:
            xml = await fetch_xml(url, params)
            policies = parse(xml)
            if not policies or any(not p.get("serv_nm") for p in policies):
                print(f"[실패] {name}: 응답에 유효한 제도 ID/이름이 없습니다.")
                failures += 1
                continue
            print(f"[성공] {name}: 제도 {len(policies)}건 조회")
            for policy in policies:
                print(f"  - {policy['serv_nm']} ({policy['serv_id']})")
        except WelfareAPIError as exc:
            print(f"[실패] {name}: {exc}")
            failures += 1
        except Exception as exc:
            print(f"[실패] {name}: 처리 오류 ({type(exc).__name__})")
            failures += 1

    print(f"\n결과: {len(providers) - failures}/{len(providers)} API 정상")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
