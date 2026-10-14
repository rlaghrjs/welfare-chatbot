import unittest
from unittest.mock import AsyncMock, patch
import test_anonymous_chat as fixtures
from app.models.platform import SyncRun, ConditionSubscription, Notification, NotificationMatch, WelfarePolicyVersion
from app.services.policy_sync_service import store_policy, collect, content_hash
from app.services.notification_service import match_conditions
from app.routers.notifications import router


class NotificationTests(unittest.TestCase):
    register = fixtures.AnonymousChatTests.register
    tearDown = fixtures.AnonymousChatTests.tearDown
    def setUp(self):
        fixtures.AnonymousChatTests.setUp(self)
        self.app.include_router(router)

    def test_version_baseline_dedup_and_ownership(self):
        with self.sessions() as db:
            for name in ('a', 'b'):
                db.add(ConditionSubscription(installation_id=self.a_id, name=name, conditions={'include_keywords': ['월세']}, event_types=['new', 'updated'], unknown_condition_policy='include'))
            run = SyncRun(source='central')
            db.add(run)
            db.flush()
            p = {'serv_id': '1', 'serv_nm': '월세 지원', 'serv_dgst': '월 10만원'}
            self.assertEqual(store_policy(db, 'central', p, run, True), 'new')
            self.assertEqual(db.query(Notification).count(), 0)
            self.assertEqual(store_policy(db, 'central', {**p, 'inq_num': 999}, run), 'unchanged')
            self.assertEqual(store_policy(db, 'central', {**p, 'serv_dgst': '월 20만원'}, run), 'updated')
            self.assertEqual(db.query(Notification).count(), 1)
            self.assertEqual(db.query(NotificationMatch).count(), 2)
            self.assertEqual(db.query(WelfarePolicyVersion).count(), 2)
            db.commit()
            notification_id = str(db.query(Notification).one().id)
        self.assertEqual(self.client.get('/api/notifications', headers=self.b).json()['items'], [])
        self.assertEqual(self.client.patch(f'/api/notifications/{notification_id}/read', headers=self.b).status_code, 404)
        self.assertEqual(self.client.get('/api/notifications', headers=self.a).json()['unread_count'], 1)
        self.assertEqual(self.client.patch(f'/api/notifications/{notification_id}/read', headers=self.a).status_code, 200)
        self.assertEqual(self.client.get('/api/notifications', headers=self.a).json()['unread_count'], 0)

    def test_matching(self):
        p = {'_source': 'local', 'ctpv_nm': '서울특별시', 'serv_nm': '청년 월세 지원', 'intrs_thema_nm_array': '주거'}
        self.assertTrue(match_conditions({'regions': ['서울특별시'], 'include_keywords': ['월세']}, p))
        self.assertTrue(match_conditions({'themes': ['040']}, p))
        self.assertFalse(match_conditions({'themes': ['100']}, p))
        self.assertFalse(match_conditions({'regions': ['인천광역시']}, p))
        self.assertFalse(match_conditions({'exclude_keywords': ['월세']}, p))
        self.assertFalse(match_conditions({'age': 24}, p, 'exclude'))
        self.assertTrue(match_conditions({'regions': ['서울특별시']}, {**p, '_source': 'central'}))

    def test_sync_failure_rolls_back_and_retry_baselines(self):
        import asyncio
        from app.services.policy_sync_service import sync_source
        from app.models.platform import WelfarePolicy
        with self.engine.connect() as connection:
            raw = connection.connection.driver_connection
            raw.create_function('hashtext', 1, lambda value: 1)
            raw.create_function('pg_try_advisory_xact_lock', 1, lambda value: True)
        rows = [{'serv_id': '1', 'serv_nm': '월세 지원'}, {'serv_id': '2', 'serv_nm': '월세 지원'}]
        with self.sessions() as db:
            with patch('app.services.policy_sync_service.collect', new=AsyncMock(return_value=rows)), patch('app.services.policy_sync_service.store_policy', side_effect=RuntimeError('test')):
                self.assertEqual(asyncio.run(sync_source(db, 'central'))['status'], 'failed')
            self.assertEqual(db.query(WelfarePolicy).count(), 0)
            self.assertEqual(db.query(SyncRun).filter_by(status='failed').count(), 1)
            with patch('app.services.policy_sync_service.collect', new=AsyncMock(return_value=rows)):
                self.assertTrue(asyncio.run(sync_source(db, 'central'))['baseline'])
                self.assertFalse(asyncio.run(sync_source(db, 'central'))['baseline'])
            self.assertEqual(db.query(WelfarePolicyVersion).count(), 2)
            self.assertEqual(db.query(Notification).count(), 0)

    def test_pagination_and_full_description(self):
        import asyncio
        long_text = '가' * 1600
        responses = [f'<root><totalCount>2</totalCount><servList><servId>1</servId><servDgst>{long_text}</servDgst></servList></root>', '<root><totalCount>2</totalCount><servList><servId>2</servId></servList></root>']
        with patch('app.services.policy_sync_service.fetch_xml', new=AsyncMock(side_effect=responses)) as fetch:
            rows = asyncio.run(collect('central'))
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]['serv_dgst'], long_text)
            self.assertEqual(fetch.await_count, 2)


if __name__ == '__main__':
    unittest.main()
