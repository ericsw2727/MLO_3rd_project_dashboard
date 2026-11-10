import json

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings

from .models import Player


@override_settings(GAME_SERVER_API_KEY='test-server-secret')
class GameIdentityTests(TestCase):
    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)

    def send(self, data=None, key='test-server-secret'):
        return self.client.post('/api/game/player-login',
            json.dumps(data if data is not None else {'member_id': 'member-001', 'display_name': '게임 회원'}),
            content_type='application/json', HTTP_AUTHORIZATION=f'Bearer {key}')

    def test_verified_identity_is_stable_and_separate_from_admin(self):
        first = self.send()
        self.assertEqual(first.status_code, 201)
        second = self.send({'member_id': 'member-001', 'display_name': '변경한 이름'})
        self.assertEqual(second.status_code, 200)
        self.assertEqual(first.json()['player']['player_id'], second.json()['player']['player_id'])
        self.assertEqual(Player.objects.get().display_name, '변경한 이름')
        self.assertEqual(Player.objects.get().source, 'live')
        self.assertFalse(get_user_model().objects.exists())
        self.assertNotIn('sessionid', second.cookies)
        self.assertEqual(self.client.get('/api/admin/players').status_code, 401)

    def test_authentication_and_disabled_integration(self):
        self.assertEqual(self.send(key='wrong').status_code, 401)
        with override_settings(GAME_SERVER_API_KEY=''):
            self.assertEqual(self.send().status_code, 503)
        self.assertFalse(Player.objects.exists())

    def test_validation_and_demo_isolation(self):
        demo = Player.objects.create(external_id='demo:member-001', display_name='데모', source='demo')
        for data in [[], {}, {'member_id': 1, 'display_name': 'name'},
                     {'member_id': 'a/b', 'display_name': 'name'},
                     {'member_id': 'a', 'display_name': ' '},
                     {'member_id': 'a', 'display_name': 'name', 'password': 'secret'}]:
            self.assertEqual(self.send(data).status_code, 400)
        self.assertEqual(self.send().status_code, 201)
        demo.refresh_from_db()
        self.assertEqual(demo.source, 'demo')
        self.assertEqual(self.client.get('/api/game/player-login').status_code, 405)
        self.assertEqual(self.client.post('/api/game/player-login', '{', content_type='application/json',
            HTTP_AUTHORIZATION='Bearer test-server-secret').status_code, 400)
        self.assertEqual(self.client.post('/api/game/player-login', {},
            HTTP_AUTHORIZATION='Bearer test-server-secret').status_code, 415)
        self.assertEqual(self.send({'member_id': 'a', 'display_name': 'x'*5000}).status_code, 413)

    def test_existing_demo_identity_cannot_be_converted(self):
        Player.objects.create(external_id='game:member:member-001', display_name='보존', source='demo')
        self.assertEqual(self.send().status_code, 409)
        self.assertEqual(Player.objects.get().display_name, '보존')
