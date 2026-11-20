"""Server part (S1, S3, S5, S5-2, game members) tests."""
import hashlib
import json
import os
import re
import shutil
import tempfile
import unittest
from datetime import timedelta
from io import StringIO
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone

from .catalog import CATALOG, CATEGORY_AREAS, classify
from .models import ContentPack, GameAccount, GameLoginRecord, GameRelease
from .mongo import database
from .releases import build_key, save_pack



class CatalogMappingTests(TestCase):
    def test_24_games_and_contract_categories(self):
        self.assertEqual(len(CATALOG), 24)
        self.assertEqual(set(CATEGORY_AREAS.values()), {'structures', 'algorithms', 'sql', 'data'})

    def test_area_comes_from_minigame_id_not_category(self):
        info = classify('st06', 'ALGO')
        self.assertEqual(info['area'], 'algorithms')
        self.assertFalse(info['category_mismatch'])
        self.assertTrue(classify('ST06', 'DS')['category_mismatch'])
        self.assertEqual(classify('XX99', 'DS')['area'], 'unmapped')

    @unittest.skipUnless(os.getenv('NODEVERSE_GAME_REPO'), 'NODEVERSE_GAME_REPO(게임 저장소 경로)를 지정하면 실행')
    def test_matches_game_learning_catalog(self):
        source = (Path(os.environ['NODEVERSE_GAME_REPO']) / 'scripts' / 'learning_catalog.gd').read_text(encoding='utf-8')
        game_ids = set(re.findall(r'"((?:ST|DS|ALG|SQL|DATA)\d{2})"', source))
        self.assertEqual(game_ids, set(CATALOG), '게임 learning_catalog.gd와 서버 catalog.py의 ID가 다릅니다')
        for code, game in CATALOG.items():
            self.assertIn(game['title'], source, f'{code} 이름이 게임 카탈로그와 다릅니다')


@override_settings(PUBLIC_BASE_URL='')
class ManifestTests(TestCase):
    def setUp(self):
        media = tempfile.mkdtemp(prefix='nodeverse-media-test-')
        self.addCleanup(shutil.rmtree, media, True)
        override = override_settings(MEDIA_ROOT=media)
        override.enable()
        self.addCleanup(override.disable)
        self.admin = get_user_model().objects.create_user('admin', password='Admin-Only!4972', display_name='Admin')

    def upload(self, version, payload=b'pack-bytes', min_build='0.3.0'):
        return save_pack(version, min_build, SimpleUploadedFile(f'{version}.pck', payload))

    def test_no_release_is_404_so_game_runs_offline(self):
        response = self.client.get('/api/game/manifest?channel=windows-stable')
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response['Cache-Control'], 'no-store')

    def test_manifest_contract_shape_cache_and_etag(self):
        GameRelease.objects.create(build_version='0.3.0', min_build='0.3.0')
        GameRelease.objects.create(build_version='0.3.10', min_build='0.3.0', notes='SQL 문제 4개 추가')
        GameRelease.objects.create(build_version='0.4.0', min_build='0.3.0', is_active=False)
        pack = self.upload('content-2026.11.19', b'x' * 1234)
        response = self.client.get('/api/game/manifest?channel=windows-stable')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Cache-Control'], 'public, max-age=60')
        data = response.json()
        self.assertEqual(data['latest_build'], '0.3.10')  # numeric, not string, comparison
        self.assertEqual(data['min_build'], '0.3.0')
        self.assertTrue(data['download_page'].endswith('/download/'))
        self.assertEqual(data['content']['version'], 'content-2026.11.19')
        entry = data['content']['packs'][0]
        self.assertEqual(entry['sha256'], hashlib.sha256(b'x' * 1234).hexdigest())
        self.assertEqual(entry['size'], 1234)
        self.assertEqual(entry['file'], 'content-2026.11.19.pck')
        self.assertTrue(entry['url'].endswith('/downloads/packs/content-2026.11.19.pck'))
        self.assertEqual(set(data), {'channel', 'latest_build', 'min_build', 'download_page', 'notes', 'content'})
        again = self.client.get('/api/game/manifest?channel=windows-stable', HTTP_IF_NONE_MATCH=response['ETag'])
        self.assertEqual(again.status_code, 304)
        file_response = self.client.get(entry['url'].split('testserver')[-1])
        self.assertEqual(file_response.status_code, 200)
        self.assertEqual(b''.join(file_response.streaming_content), b'x' * 1234)
        self.assertIn('immutable', file_response['Cache-Control'])
        self.assertEqual(pack.size, 1234)

    def test_disabling_pack_rolls_back_to_previous(self):
        GameRelease.objects.create(build_version='0.3.0', min_build='0.3.0')
        self.upload('content-2026.11.12', b'old')
        bad = self.upload('content-2026.11.19', b'new')
        self.assertEqual(self.client.get('/api/game/manifest').json()['content']['version'], 'content-2026.11.19')
        self.client.force_login(self.admin)
        self.client.post(f'/staff/releases/packs/{bad.pk}/toggle/')
        self.assertEqual(self.client.get('/api/game/manifest').json()['content']['version'], 'content-2026.11.12')
        self.assertTrue(ContentPack.objects.get(pk=bad.pk).file.storage.exists(bad.file.name))  # file kept

    def test_admin_upload_computes_hash_and_rejects_anonymous(self):
        self.assertEqual(self.client.get('/staff/releases/').status_code, 302)
        self.client.force_login(self.admin)
        response = self.client.post('/staff/releases/', {
            'form': 'pack', 'pack-version': 'content-2026.11.20', 'pack-min_build': '0.3.0',
            'pack-file': SimpleUploadedFile('anything.pck', b'abc')})
        self.assertEqual(response.status_code, 302)
        pack = ContentPack.objects.get(version='content-2026.11.20')
        self.assertEqual(pack.sha256, hashlib.sha256(b'abc').hexdigest())
        response = self.client.post('/staff/releases/', {'form': 'release', 'release-channel': 'windows-stable',
                                    'release-build_version': '0.3.1', 'release-min_build': '0.3.2'})
        self.assertEqual(response.status_code, 200)  # min_build above build_version rejected
        self.assertFalse(GameRelease.objects.exists())

    def test_dashboard_download_tab(self):
        self.assertEqual(self.client.get('/staff/download/').status_code, 302)
        self.client.force_login(self.admin)
        empty = self.client.get('/staff/download/')
        self.assertContains(empty, '공개된 릴리스가 없습니다')
        GameRelease.objects.create(build_version='0.3.0', min_build='0.3.0', is_active=False)
        GameRelease.objects.create(build_version='0.3.1', min_build='0.3.0', notes='새 문제',
                                   package_url='https://example.com/nodeverse.zip')
        self.upload('content-2026.11.19')
        page = self.client.get('/staff/download/')
        self.assertContains(page, 'NODEVERSE 0.3.1')
        self.assertContains(page, 'https://example.com/nodeverse.zip')
        self.assertContains(page, '/api/game/manifest?channel=windows-stable')
        self.assertContains(page, 'content-2026.11.19.pck')
        self.assertEqual([r.link for r in page.context['history']], ['https://example.com/nodeverse.zip', None])

    def test_download_page_and_build_key(self):
        self.assertEqual(self.client.get('/download/').status_code, 200)
        self.assertLess(build_key('0.3.9'), build_key('0.3.10'))


class GameAuthTests(TestCase):
    """The team's /api/game/auth/* contract (used by the Godot client) plus server-side history and limits."""

    def setUp(self):
        cache.clear()

    def post(self, path, ip='10.0.0.5', **data):
        return self.client.post(path, json.dumps(data), content_type='application/json', REMOTE_ADDR=ip)

    def test_register_login_save_and_history(self):
        response = self.post('/api/game/auth/register', username='Player_01', password='secret-pass',
                             recovery_key='Me@Example.com', install_id='inst-1', build_version='0.3.0')
        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertTrue(body['success'])
        self.assertEqual(set(body), {'success', 'message', 'username', 'player_id', 'save_data'})
        self.assertFalse(body['save_data']['has_saved_game'])
        account = GameAccount.objects.get(username='Player_01')
        self.assertNotIn('secret-pass', account.password_hash)
        self.assertEqual(account.recovery_key, 'me@example.com')
        self.assertEqual(self.post('/api/game/auth/register', username='Player_01', password='xyz').status_code, 409)
        self.assertEqual(self.post('/api/game/auth/login', username='Player_01', password='wrong').status_code, 401)
        ok = self.post('/api/game/auth/login', username='Player_01', password='secret-pass', install_id='inst-2')
        self.assertEqual(ok.status_code, 200)
        self.assertEqual(ok.json()['player_id'], body['player_id'])

        saved = self.post('/api/game/auth/save', username='Player_01',
                          save_data={'score': 120, 'minigame_cleared': {'ST01': 3}, 'has_saved_game': True})
        self.assertEqual(saved.json(), {'success': True, 'message': '클라우드 저장 완료'})
        again = self.post('/api/game/auth/login', username='Player_01', password='secret-pass').json()
        self.assertEqual(again['save_data']['minigame_cleared'], {'ST01': 3})
        self.assertIn('last_saved', again['save_data'])

        rows = list(GameLoginRecord.objects.order_by('pk').values_list('kind', 'success', 'failure_reason', 'install_id'))
        self.assertEqual(rows, [('register', True, '', 'inst-1'), ('register', False, 'username_taken', ''),
                                ('login', False, 'wrong_password', ''), ('login', True, '', 'inst-2'),
                                ('login', True, '', '')])
        self.assertEqual(GameLoginRecord.objects.filter(player=account.player).count(), 4)

    def test_find_id_and_reset_password(self):
        self.post('/api/game/auth/register', username='withkey', password='pw1', recovery_key='nick')
        self.post('/api/game/auth/register', username='nokey', password='pw1')
        found = self.post('/api/game/auth/find-id', recovery_key='NICK')
        self.assertEqual(found.status_code, 200)
        self.assertEqual(found.json()['usernames'], ['withkey'])
        self.assertEqual(self.post('/api/game/auth/find-id', recovery_key='nobody').status_code, 404)

        self.assertEqual(self.post('/api/game/auth/reset-password', username='withkey', recovery_key='bad',
                                   new_password='pw2').status_code, 403)
        self.assertEqual(self.post('/api/game/auth/reset-password', username='withkey', recovery_key='nick',
                                   new_password='pw2').status_code, 200)
        self.assertEqual(self.post('/api/game/auth/login', username='withkey', password='pw2').status_code, 200)
        # An account without a recovery key cannot be reset (and taken over) by anyone.
        self.assertEqual(self.post('/api/game/auth/reset-password', username='nokey', recovery_key='anything',
                                   new_password='hacked').status_code, 403)
        self.assertEqual(self.post('/api/game/auth/login', username='nokey', password='hacked').status_code, 401)
        self.assertEqual(GameAccount.objects.get(username='nokey').recovery_key, '')
        kinds = set(GameLoginRecord.objects.values_list('kind', flat=True))
        self.assertTrue({'find_id', 'reset'} <= kinds)

    def test_validation(self):
        self.assertEqual(self.post('/api/game/auth/register', username='a', password='pw1').status_code, 400)
        self.assertEqual(self.post('/api/game/auth/register', username='Guest', password='pw1').status_code, 400)
        self.assertEqual(self.post('/api/game/auth/login', username='x').status_code, 400)
        self.assertEqual(self.post('/api/game/auth/save', username='x', save_data='nope').status_code, 400)
        self.assertEqual(self.client.get('/api/game/auth/login').status_code, 405)
        bad = self.client.post('/api/game/auth/login', 'not json', content_type='application/json')
        self.assertEqual(bad.status_code, 400)

    def test_failed_logins_are_rate_limited(self):
        self.post('/api/game/auth/register', username='target', password='secret-pass')
        for n in range(10):
            self.post('/api/game/auth/login', ip=f'10.0.1.{n}', username='target', password='bad')
        locked = self.post('/api/game/auth/login', username='target', password='secret-pass')
        self.assertEqual(locked.status_code, 429)
        self.assertFalse(locked.json()['success'])

    def test_requests_per_ip_are_rate_limited(self):
        codes = [self.post('/api/game/auth/find-id', recovery_key='x').status_code for _ in range(31)]
        self.assertEqual(codes[-1], 429)
        self.assertNotIn(429, codes[:30])


@override_settings(DEBUG=True)
class LiveApiTests(TestCase):
    def setUp(self):
        self.assertTrue(database().name.startswith('nodeverse_test_'))
        self.admin = get_user_model().objects.create_user('admin', password='Admin-Only!4972', display_name='Admin')
        self.learner = get_user_model().objects.create_user('old', password='Learner-Only!4972', display_name='Old', role='learner')
        call_command('seed_rt', '--minutes', '40', stdout=StringIO())

    def tearDown(self):
        call_command('seed_rt', '--clear', stdout=StringIO())

    def test_permissions_and_minutes_range(self):
        self.assertEqual(self.client.get('/api/admin/live/summary').status_code, 401)
        self.client.force_login(self.learner)  # legacy non-admin accounts are never let in
        self.assertIn(self.client.get('/api/admin/live/summary').status_code, (401, 403))
        self.client.force_login(self.admin)
        for path in ('/api/admin/live/minigames', '/api/admin/live/alerts', '/api/admin/live/updates'):
            self.assertEqual(self.client.get(path + '?minutes=0').status_code, 400)
            self.assertEqual(self.client.get(path + '?minutes=181').status_code, 400)
            self.assertEqual(self.client.get(path + '?minutes=abc').status_code, 400)

    def test_mock_data_through_apis(self):
        self.client.force_login(self.admin)
        summary = self.client.get('/api/admin/live/summary')
        self.assertEqual(summary.status_code, 200)
        self.assertIn('no-store', summary['Cache-Control'])
        self.assertFalse(summary.json()['stale'])
        games = self.client.get('/api/admin/live/minigames?minutes=30').json()
        self.assertEqual(len(games['games']), 24)
        self.assertTrue(games['rows'])
        st06 = next(r for r in games['rows'] if r['minigame_id'] == 'ST06')
        self.assertEqual(st06['area'], 'algorithms')
        alerts = self.client.get('/api/admin/live/alerts?minutes=60').json()['alerts']
        self.assertTrue(alerts and all(a['alert'] for a in alerts))
        self.assertEqual([a['window_start'] for a in alerts], sorted([a['window_start'] for a in alerts], reverse=True))
        updates = self.client.get('/api/admin/live/updates?minutes=60').json()
        self.assertTrue(updates['windows'] and updates['versions'])
        self.assertIn('review', updates['pack_warning'])
        self.assertEqual(self.client.get('/staff/live/').status_code, 200)
        self.assertEqual(self.client.get('/staff/live/?tab=updates').status_code, 200)

    def test_stale_summary(self):
        database().rt_summary.update_one({'_id': 'global'}, {'$set': {'updated_at': timezone.now() - timedelta(seconds=45)}})
        self.client.force_login(self.admin)
        self.assertTrue(self.client.get('/api/admin/live/summary').json()['stale'])

    def test_members_page_shows_accounts_with_cloud_save_progress(self):
        cache.clear()

        def post(path, **data):
            return self.client.post(path, json.dumps(data), content_type='application/json')

        post('/api/game/auth/register', username='member1', password='secret-pass', install_id='inst-1')
        post('/api/game/auth/save', username='member1',
             save_data={'score': 50, 'minigame_cleared': {'st01': 2, 'ST06': 3, 'stack_room': 1}, 'zone': 'DS'})
        self.client.force_login(self.admin)
        page = self.client.get('/staff/members/')
        self.assertEqual(page.status_code, 200)
        row = page.context['rows'][0]
        self.assertEqual(row['account'].username, 'member1')
        self.assertEqual(row['progress']['cleared'], 3)
        self.assertEqual(row['progress']['stars'], 6)
        self.assertEqual(row['progress']['other'], {'stack_room': 1})
        detail = self.client.get(f"/staff/members/{row['player'].pk}/")
        self.assertEqual(detail.status_code, 200)
        self.assertContains(detail, 'stack_room')
        self.assertEqual([r.kind for r in detail.context['history']], ['register'])
        # One sidebar entry: account view and learning view link to each other for the same person.
        pid = row['player'].pk
        self.assertContains(page, 'href="/staff/players/"')
        self.assertContains(detail, f'href="/staff/players/{pid}/"')
        learning = self.client.get(f'/staff/players/{pid}/')
        self.assertEqual(learning.status_code, 200)
        self.assertContains(learning, f'href="/staff/members/{pid}/"')
        self.assertNotContains(page, '<span>게임 회원</span>')

    def test_member_detail_shows_pipeline_play_by_install_id(self):
        cache.clear()
        self.client.post('/api/game/auth/register', json.dumps({'username': 'player9', 'password': 'secret-pass',
                                                                'install_id': 'inst-play-9'}), content_type='application/json')
        account = GameAccount.objects.get(username='player9')
        now = timezone.now()
        events = database().pipeline_learning_events
        events.delete_many({'player_id': {'$in': ['inst-play-9', 'someone-else']}})
        events.insert_many([
            {'_id': 'p9-1', 'player_id': 'inst-play-9', 'minigame_id': 'ALG01', 'event_type': 'attempt_started', 'occurred_at': now - timedelta(seconds=5)},
            {'_id': 'p9-2', 'player_id': 'inst-play-9', 'minigame_id': 'ALG01', 'event_type': 'attempt_failed', 'occurred_at': now - timedelta(seconds=4),
             'details': {'operation': 'wrong_move', 'failure_reason': '교환하지 않았어요'}},
            {'_id': 'p9-3', 'player_id': 'inst-play-9', 'minigame_id': 'ALG01', 'event_type': 'attempt_succeeded', 'occurred_at': now},
            {'_id': 'other', 'player_id': 'someone-else', 'minigame_id': 'ST01', 'event_type': 'attempt_started', 'occurred_at': now},
        ])
        self.client.force_login(self.admin)
        page = self.client.get(f'/staff/members/{account.player_id}/')
        play = page.context['play']
        self.assertEqual(play['total'], 3)
        self.assertEqual([(g['code'], g['attempts'], g['succeeded'], g['failed'], g['rate']) for g in play['games']], [('ALG01', 1, 1, 1, 50)])
        self.assertEqual(play['events'][0]['label'], '시도 성공')
        self.assertContains(page, '교환하지 않았어요')
        self.assertNotContains(page, 'someone-else')
        events.delete_many({'_id': {'$in': ['p9-1', 'p9-2', 'p9-3', 'other']}})

    def test_events_page_reads_pipeline_events_and_names_members(self):
        cache.clear()
        self.client.post('/api/game/auth/register', json.dumps({'username': 'player7', 'password': 'secret-pass',
                                                                'install_id': 'inst-ev-7'}), content_type='application/json')
        account = GameAccount.objects.get(username='player7')
        now = timezone.now()
        events = database().pipeline_learning_events
        ids = ['e7-1', 'e7-2', 'e7-3', 'e7-old']
        events.delete_many({'_id': {'$in': ids}})
        events.insert_many([
            {'_id': 'e7-1', 'player_id': 'inst-ev-7', 'minigame_id': 'SQL01', 'event_type': 'hint_used', 'occurred_at': now - timedelta(seconds=2), 'sequence': 1},
            {'_id': 'e7-2', 'player_id': 'inst-ev-7', 'minigame_id': 'SQL01', 'event_type': 'attempt_succeeded', 'occurred_at': now, 'sequence': 2},
            {'_id': 'e7-3', 'player_id': 'stranger-device', 'minigame_id': 'ST01', 'event_type': 'attempt_started', 'occurred_at': now - timedelta(seconds=1)},
            {'_id': 'e7-old', 'player_id': 'inst-ev-7', 'minigame_id': 'SQL01', 'event_type': 'attempt_started', 'occurred_at': now - timedelta(days=30)},
        ])
        self.client.force_login(self.admin)
        page = self.client.get('/staff/events/')
        self.assertEqual(page.status_code, 200)
        rows = [(r['code'], r['kind'], r['member']['name'] if r['member'] else None) for r in page.context['rows'] if r['code'] in ('SQL01', 'ST01')]
        self.assertEqual(rows, [('SQL01', 'attempt_succeeded', 'player7'), ('ST01', 'attempt_started', None), ('SQL01', 'hint_used', 'player7')])
        self.assertContains(page, f'/staff/members/{account.player_id}/#play')
        self.assertContains(page, '미가입 기기')
        only = self.client.get(f'/staff/events/?member={account.player_id}&kind=hint_used')
        self.assertEqual([r['kind'] for r in only.context['rows']], ['hint_used'])
        events.delete_many({'_id': {'$in': ids}})

    def test_overview_counts_pipeline_play_of_members(self):
        cache.clear()
        self.client.post('/api/game/auth/register', json.dumps({'username': 'player5', 'password': 'secret-pass',
                                                                'install_id': 'inst-ov-5'}), content_type='application/json')
        now = timezone.now()
        run, attempt, session = 'aaaaaaaa-0000-4000-8000-000000000001', 'aaaaaaaa-0000-4000-8000-000000000002', 'aaaaaaaa-0000-4000-8000-000000000003'
        base = {'player_id': 'inst-ov-5', 'minigame_id': 'ST01', 'session_id': session, 'run_id': run, 'content_version': 'base'}
        rows = [('problem_started', None, {}), ('attempt_started', attempt, {}), ('operation_failed', attempt, {'operation': 'push', 'failure_reason': 'full'}),
                ('hint_used', None, {}), ('attempt_succeeded', attempt, {}), ('problem_completed', None, {})]
        docs = [{**base, '_id': f'ov-{n}', 'sequence': n, 'event_type': kind, 'attempt_id': att, 'details': details,
                 'occurred_at': now - timedelta(seconds=60 - n)} for n, (kind, att, details) in enumerate(rows, 1)]
        docs.append({'_id': 'ov-stranger', 'player_id': 'not-a-member', 'minigame_id': 'ST01', 'run_id': 'x', 'event_type': 'problem_started', 'occurred_at': now})
        events = database().pipeline_learning_events
        events.delete_many({'_id': {'$in': [d['_id'] for d in docs]}})
        events.insert_many(docs)
        self.client.force_login(self.admin)
        page = self.client.get('/staff/')
        self.assertEqual(page.status_code, 200)
        stats, learning = page.context['stats'], page.context['learning']
        self.assertEqual((stats['total'], stats['attempts'], stats['hints'], stats['failures']), (6, 1, 1, 1))
        self.assertEqual((learning['runs'], learning['completed']), (1, 1))
        self.assertEqual(learning['failures'], [{'operation': 'push', 'reason': 'full', 'count': 1}])
        st01 = next(g for g in page.context['catalog']['games'] if g['code'] == 'ST01')
        self.assertEqual((st01['runs'], st01['completed'], st01['hints']), (1, 1, 1))
        self.assertEqual(self.client.get('/staff/games/?game_id=ST01&category=structures').status_code, 200)
        self.assertEqual(self.client.get('/staff/players/').status_code, 200)
        events.delete_many({'_id': {'$in': [d['_id'] for d in docs]}})

    def test_overview_skips_pipeline_runs_already_in_legacy_collections(self):
        cache.clear()
        self.client.post('/api/game/auth/register', json.dumps({'username': 'player4', 'password': 'secret-pass',
                                                                'install_id': 'inst-dup-4'}), content_type='application/json')
        run = 'bbbbbbbb-0000-4000-8000-000000000001'
        db = database()
        db.pipeline_learning_events.delete_many({'_id': 'dup-1'})
        db.problem_runs.delete_many({'_id': run})
        db.pipeline_learning_events.insert_one({'_id': 'dup-1', 'player_id': 'inst-dup-4', 'minigame_id': 'ST01', 'run_id': run,
                                                'event_type': 'problem_started', 'occurred_at': timezone.now()})
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get('/staff/').context['learning']['runs'], 1)
        db.problem_runs.insert_one({'_id': run, 'session_id': 'not-loaded', 'task_id': 'x'})  # projected by the pipeline
        self.assertEqual(self.client.get('/staff/').context['learning']['runs'], 0)
        db.pipeline_learning_events.delete_many({'_id': 'dup-1'})
        db.problem_runs.delete_many({'_id': run})
