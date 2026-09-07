import os
import unittest
from unittest.mock import AsyncMock, Mock, patch
from urllib.parse import parse_qs, urlsplit

# Isolate tests from credentials and databases configured in .env.
os.environ.update(
    DATABASE_URL="sqlite://", WELFARE_API_URL="https://example.com/central",
    WELFARE_API_KEY="test-secret", LOCAL_WELFARE_API_URL="https://example.com/local",
    LOCAL_WELFARE_API_KEY="test-secret", OPENAI_API_KEY="test-key",
)

import httpx
from app.services import welfare_api_common as common
from app.services import welfare_service as central
from app.services import local_welfare_service as local


class WelfareDataTests(unittest.TestCase):
    def test_zero_age_and_provider_parameters(self):
        for build in (central.build_welfare_params, local.build_local_welfare_params):
            self.assertEqual(build({"age": 0})["age"], 0)
            self.assertNotIn("age", build({"age": None}))
        self.assertEqual(local.build_local_welfare_params({"ctpvNm": "서울"})["ctpvNm"], "서울")

    def test_url_keeps_filters_but_removes_key(self):
        url = common.build_safe_request_url(
            "https://example.com/api?existing=1&serviceKey=old",
            {"serviceKey": "test-secret", "searchWrd": "청년 지원"},
        )
        params = parse_qs(urlsplit(url).query)
        self.assertEqual(params["serviceKey"], ["[REDACTED]"])
        self.assertEqual(params["searchWrd"], ["청년 지원"])
        self.assertEqual(params["existing"], ["1"])
        self.assertNotIn("test-secret", url)

    def test_parsers_normalize_and_deduplicate(self):
        xml = '''<root><servList><servId> a </servId><servNm>&lt;b&gt;지원&lt;/b&gt;</servNm>
        <inqNum>invalid</inqNum><servDgst>  내용   설명 </servDgst></servList>
        <servList><servId>a</servId><servNm>duplicate</servNm></servList>
        <servList><servNm>missing id</servNm></servList></root>'''
        for parse in (central.parse_welfare_xml, local.parse_local_welfare_xml):
            result = parse(xml)
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]["serv_id"], "a")
            self.assertEqual(result[0]["serv_nm"], "지원")
            self.assertEqual(result[0]["serv_dgst"], "내용 설명")
            self.assertIsNone(result[0]["inq_num"])
            self.assertEqual(parse("<root/>"), [])

    def test_invalid_and_gateway_error_xml(self):
        for xml in ("<broken", "<OpenAPI_ServiceResponse><cmmMsgHeader><errMsg>secret</errMsg></cmmMsgHeader></OpenAPI_ServiceResponse>"):
            with self.assertRaises(common.WelfareAPIError) as error:
                central.parse_welfare_xml(xml)
            self.assertNotIn("secret", str(error.exception))

    @patch.object(common, "WelfareApiResult")
    def test_save_failure_rolls_back(self, model):
        db = Mock()
        db.commit.side_effect = RuntimeError("database unavailable")
        with self.assertRaises(RuntimeError):
            common.save_api_results(db, "session", "query", "https://example.com?serviceKey=secret", {}, [{"serv_id": "a"}], "central_welfare")
        db.rollback.assert_called_once()
        self.assertNotIn("secret", model.call_args.kwargs["request_url"])

    @patch.object(common, "WelfareApiResult")
    def test_save_uses_provider_and_one_batch(self, model):
        db = Mock()
        result = local.save_local_welfare_api_results(db, "session", "query", "https://example.com", {}, [{"serv_id": "a"}])
        self.assertEqual(model.call_args.kwargs["source"], "local_welfare")
        db.add_all.assert_called_once_with(result)
        db.commit.assert_called_once()
        db.refresh.assert_not_called()


class WelfareTransportTests(unittest.IsolatedAsyncioTestCase):
    async def test_http_status_failure_is_safe(self):
        response = httpx.Response(503, request=httpx.Request("GET", "https://example.com?serviceKey=secret"))
        with patch.object(common.httpx, "AsyncClient") as client:
            client.return_value.__aenter__.return_value.get = AsyncMock(return_value=response)
            with self.assertRaises(common.WelfareAPIError) as caught:
                await common.fetch_xml("https://example.com", {})
            self.assertNotIn("secret", str(caught.exception))

    async def test_api_error_handler_and_zero_age_profile(self):
        from app.core.exception_handlers import welfare_api_error_handler
        from app.routers.chat import is_searchable_intent, merge_profile_into_intent
        from app.schemas.chat import WelfareProfile

        response = await welfare_api_error_handler(None, common.WelfareAPIError("upstream failure"))
        self.assertEqual(response.status_code, 502)
        self.assertTrue(is_searchable_intent({"age": 0}))
        self.assertEqual(merge_profile_into_intent({}, WelfareProfile(age=0))["age"], 0)
        self.assertEqual(merge_profile_into_intent({"age": 0}, WelfareProfile(age=25))["age"], 0)

    async def test_http_failures_are_safe(self):
        for error in (httpx.ConnectError("secret"), httpx.ReadTimeout("secret")):
            with patch.object(common.httpx, "AsyncClient") as client:
                client.return_value.__aenter__.return_value.get = AsyncMock(side_effect=error)
                with self.assertRaises(common.WelfareAPIError) as caught:
                    await common.fetch_xml("https://example.com", {"serviceKey": "secret"})
                self.assertNotIn("secret", str(caught.exception))

    async def test_fetch_parse_save_contract(self):
        for module, fetch_name, save_name in (
            (central, "fetch_save_and_return", "save_welfare_api_results"),
            (local, "fetch_local_save_and_return", "save_local_welfare_api_results"),
        ):
            with patch.object(module, "fetch_xml", new=AsyncMock(return_value="<root><servList><servId>a</servId></servList></root>")), patch.object(module, save_name, return_value=[Mock()]) as save:
                result = await getattr(module, fetch_name)(Mock(), "session", "query", {})
                self.assertEqual(result["saved_count"], 1)
                self.assertEqual(result["policies"][0]["serv_id"], "a")
                self.assertNotIn("test-secret", result["request_url"])
                save.assert_called_once()


if __name__ == "__main__":
    unittest.main()
