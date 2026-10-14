"""Behavior tests use isolated SQLite; no live API, account or production DB calls."""
import os
import unittest
import uuid
from unittest.mock import AsyncMock, patch

os.environ.update(DATABASE_URL="sqlite://", WELFARE_API_URL="https://example.com/central",
                  WELFARE_API_KEY="test", LOCAL_WELFARE_API_URL="https://example.com/local",
                  LOCAL_WELFARE_API_KEY="test", OPENAI_API_KEY="test")

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.db.database import Base, get_db
import app.models
from app.models.platform import (
    AppInstallation, Profile, ConditionSubscription, WelfarePolicy, WelfarePolicyVersion,
    ChatSearchResult, Notification, NotificationMatch,
)
from app.models.chat_session import ChatSession
from app.models.chat_message import ChatMessage
from app.routers import chat, installations, subscriptions
from app.core.exception_handlers import welfare_api_error_handler
from app.services.welfare_api_common import WelfareAPIError


@compiles(JSONB, "sqlite")
def sqlite_jsonb(type_, compiler, **kw):
    return "JSON"


class AnonymousChatTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        @event.listens_for(self.engine, "connect")
        def foreign_keys(connection, _):
            connection.execute("PRAGMA foreign_keys=ON")
        Base.metadata.create_all(self.engine)
        self.sessions = sessionmaker(self.engine, autoflush=False)
        def database():
            with self.sessions() as session:
                yield session
        self.app = FastAPI()
        self.app.include_router(chat.router)
        self.app.include_router(installations.router)
        self.app.include_router(subscriptions.router)
        self.app.add_exception_handler(WelfareAPIError, welfare_api_error_handler)
        self.app.dependency_overrides[get_db] = database
        self.client = TestClient(self.app)
        self.a, self.a_id = self.register()
        self.b, self.b_id = self.register()
        self.nlp = patch.object(chat, "analyze_message", return_value={})
        self.nlp.start()

    def tearDown(self):
        self.nlp.stop()
        self.client.close()
        self.engine.dispose()

    def register(self):
        row_id = uuid.uuid4()
        secret = uuid.uuid4().hex + uuid.uuid4().hex
        result = self.client.post("/api/installations", json={"installation_id": str(row_id), "secret": secret})
        self.assertEqual(result.status_code, 201, result.text)
        return {"Authorization": f"Bearer {row_id}.{secret}"}, row_id

    def message(self, headers=None, **body):
        return self.client.post("/api/chat/message", headers=headers or self.a, json={"message": "안녕하세요", **body})

    def test_registration_is_retryable_and_secret_cannot_be_replaced(self):
        credential = self.a["Authorization"].split()[1]
        row_id, secret = credential.split(".")
        self.assertEqual(self.client.post("/api/installations", json={"installation_id": row_id, "secret": secret}).status_code, 201)
        self.assertEqual(self.client.post("/api/installations", json={"installation_id": row_id, "secret": "x" * 64}).status_code, 409)
        with self.sessions() as db:
            self.assertNotEqual(db.get(AppInstallation, self.a_id).token_hash, secret)

    def test_uuid_alone_or_wrong_secret_does_not_grant_access(self):
        for headers in ({}, {"Authorization": f"Bearer {self.a_id}"}, {"Authorization": f"Bearer {self.a_id}.wrong"}):
            self.assertEqual(self.client.get("/api/chat/sessions", headers=headers).status_code, 401)

    def test_first_message_creates_session_followup_reuses_it(self):
        response = self.message()
        self.assertEqual(response.status_code, 200, response.text)
        session_id = response.json()["session_id"]
        second = self.message(session_id=session_id, message="추가 질문")
        self.assertEqual(second.json()["session_id"], session_id)
        sessions = self.client.get("/api/chat/sessions", headers=self.a).json()
        self.assertEqual(len(sessions), 1)
        self.assertNotIn("status", sessions[0])
        detail = self.client.get(f"/api/chat/session/{session_id}", headers=self.a).json()
        self.assertEqual([m["role"] for m in detail["messages"]], ["user", "assistant", "user", "assistant"])

    def test_cross_installation_read_write_delete_are_denied(self):
        session_id = self.message().json()["session_id"]
        self.assertEqual(self.client.get("/api/chat/sessions", headers=self.b).json(), [])
        url = f"/api/chat/session/{session_id}"
        self.assertEqual(self.client.get(url, headers=self.b).status_code, 404)
        self.assertEqual(self.message(headers=self.b, session_id=session_id).status_code, 404)
        self.assertEqual(self.client.delete(url, headers=self.b).status_code, 404)

    def test_blank_message_does_not_create_session(self):
        self.assertEqual(self.message(message="  ").status_code, 422)
        self.assertEqual(self.client.get("/api/chat/sessions", headers=self.a).json(), [])

    def test_provider_failure_leaves_no_half_created_session(self):
        with patch.object(chat, "analyze_message", return_value={"searchWrd": "월세"}), patch.object(chat, "fetch_xml", new=AsyncMock(side_effect=WelfareAPIError("요청 실패"))):
            self.assertEqual(self.message().status_code, 502)
        self.assertEqual(self.client.get("/api/chat/sessions", headers=self.a).json(), [])

    def test_cards_are_restored_and_message_order_is_preserved(self):
        xml = "<root><servList><servId>p1</servId><servNm>월세 지원</servNm></servList></root>"
        with patch.object(chat, "analyze_message", return_value={"searchWrd": "월세"}), patch.object(chat, "fetch_xml", new=AsyncMock(return_value=xml)):
            response = self.message()
        session_id = response.json()["session_id"]
        detail = self.client.get(f"/api/chat/session/{session_id}", headers=self.a).json()
        self.assertEqual([m["message_type"] for m in detail["messages"]], ["text", "text", "welfare_cards", "welfare_cards"])
        self.assertEqual(detail["messages"][2]["message_metadata"]["policies"][0]["serv_id"], "p1")

    def subscription(self, headers=None, **extra):
        return self.client.post("/api/subscriptions", headers=headers or self.a,
                                json={"name": "주거 지원", "conditions": {"themes": ["040"]}, **extra})

    def seed_policy(self):
        with self.sessions() as db:
            policy = WelfarePolicy(source="central", external_id="P1", name="정책", content_hash="a" * 64, raw_data={})
            db.add(policy); db.flush()
            version = WelfarePolicyVersion(policy_id=policy.id, version_no=1, change_type="new", snapshot={})
            db.add(version); db.commit()
            return version.id

    def test_chat_delete_preserves_subscription_and_catalog(self):
        session_id = self.message().json()["session_id"]
        self.assertEqual(self.subscription().status_code, 201)
        version_id = self.seed_policy()
        with self.sessions() as db:
            message = db.scalar(select(ChatMessage).where(ChatMessage.session_id == uuid.UUID(session_id)))
            db.add(ChatSearchResult(message_id=message.id, policy_version_id=version_id, rank=1)); db.commit()
        self.assertEqual(self.client.delete(f"/api/chat/session/{session_id}", headers=self.a).status_code, 204)
        with self.sessions() as db:
            self.assertEqual(db.query(ChatMessage).count(), 0)
            self.assertEqual(db.query(ChatSearchResult).count(), 0)
            self.assertEqual(db.query(ConditionSubscription).count(), 1)
            self.assertEqual(db.query(WelfarePolicyVersion).count(), 1)

    def test_subscriptions_and_profiles_are_owner_scoped(self):
        profile = self.client.post("/api/profiles", headers=self.a, json={"name": "본인", "region": "서울특별시"}).json()
        self.assertEqual(self.subscription(headers=self.b, profile_id=profile["id"]).status_code, 404)
        sub = self.subscription(profile_id=profile["id"])
        self.assertEqual(sub.status_code, 201)
        sub_id = sub.json()["id"]
        self.assertEqual(self.client.get("/api/subscriptions", headers=self.b).json(), [])
        self.assertEqual(self.client.delete(f"/api/subscriptions/{sub_id}", headers=self.b).status_code, 404)
        self.assertEqual(self.client.delete(f"/api/profiles/{profile['id']}", headers=self.a).status_code, 409)
        self.assertEqual(self.client.delete(f"/api/subscriptions/{sub_id}", headers=self.a).status_code, 204)
        self.assertEqual(self.client.delete(f"/api/profiles/{profile['id']}", headers=self.a).status_code, 204)

    def test_invalid_conditions_are_rejected(self):
        for conditions in ({"age": -1}, {"invented": True}, {"include_keywords": ["월세"], "exclude_keywords": ["월세"]}, {}):
            self.assertEqual(self.subscription(conditions=conditions).status_code, 422)

    def test_legacy_sessions_are_not_claimed_by_new_installations(self):
        with self.sessions() as db:
            db.add(ChatSession(title="과거 기록")); db.commit()
        self.assertEqual(self.client.get("/api/chat/sessions", headers=self.a).json(), [])

    def test_full_installation_deletion_preserves_other_installation_and_catalog(self):
        self.message(); self.message(headers=self.b)
        profile = self.client.post("/api/profiles", headers=self.a, json={"name": "본인"}).json()
        sub = self.subscription(profile_id=profile["id"]).json()
        version_id = self.seed_policy()
        with self.sessions() as db:
            notification = Notification(installation_id=self.a_id, policy_version_id=version_id, title="알림", body="변경")
            db.add(notification); db.flush()
            db.add(NotificationMatch(notification_id=notification.id, subscription_id=uuid.UUID(sub["id"]), conditions_snapshot={}, match_reason={}))
            db.commit()
        self.assertEqual(self.client.delete("/api/installations/me", headers=self.a).status_code, 204)
        self.assertEqual(self.client.get("/api/chat/sessions", headers=self.a).status_code, 401)
        self.assertEqual(len(self.client.get("/api/chat/sessions", headers=self.b).json()), 1)
        with self.sessions() as db:
            for model in (Profile, ConditionSubscription, Notification, NotificationMatch):
                self.assertEqual(db.query(model).count(), 0)
            self.assertEqual(db.query(WelfarePolicy).count(), 1)


if __name__ == "__main__":
    unittest.main()
