import importlib
import json
import uuid
from datetime import timedelta
from io import StringIO
from types import SimpleNamespace
from unittest.mock import patch
from django.apps import apps
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db import connection
from django.test import TestCase, Client, override_settings
from django.utils import timezone
from pymongo.errors import ServerSelectionTimeoutError
from .models import Player, PlaySession, LearningTask, TaskRun, SolveAttempt, BehaviorEvent
from .mongo import database, collection, insert_record, get_record, initialize_indexes, LOG_MODELS
from .recording import create_record, record_event, finalize_run, finish_record, validate_metadata


class MongoAnalyticsTests(TestCase):
    def setUp(self):
        self.assertTrue(database().name.startswith('nodeverse_test_'))
        for model in LOG_MODELS:
            collection(model).delete_many({})
        initialize_indexes()
        self.admin = get_user_model().objects.create_user('admin', password='Admin-Only!4972',display_name='Admin')
        self.client.force_login(self.admin)
        self.member = Player.objects.create(external_id='test:member',display_name='Member',source='live')
        self.now = timezone.now().replace(microsecond=0)-timedelta(minutes=5)
        self.session = create_record(PlaySession(player=self.member,topic='stack',started_at=self.now,status='in_progress'))[0]
        self.problem = create_record(LearningTask(task_id='stack-01',content_version='1.0',title='Stack',topic='stack'))[0]
        self.run = create_record(TaskRun(session=self.session,task=self.problem,started_at=self.now,status='in_progress'))[0]
        self.attempt = create_record(SolveAttempt(run=self.run,number=1,started_at=self.now,outcome='in_progress'))[0]

    def event(self, kind, seq, seconds, **extra):
        return record_event(id=uuid.uuid4(),session=self.session,run=self.run,attempt=self.attempt if kind.startswith(('attempt_','operation_')) else None,
                            sequence=seq,event_type=kind,occurred_at=self.now+timedelta(seconds=seconds),**extra)

    def solve(self):
        self.event('task_started',1,0)
        self.event('attempt_started',2,1)
        self.event('operation_succeeded',3,10,operation='pop')
        self.event('attempt_succeeded',4,20)
        finish_record(SolveAttempt,self.attempt.pk,'success',self.now+timedelta(seconds=20))
        self.event('task_completed',5,30)
        finalize_run(self.run,'completed',self.now+timedelta(seconds=30))
        finish_record(PlaySession,self.session.pk,'completed',self.now+timedelta(seconds=35))

    def test_logs_have_no_sql_tables_and_members_remain_sql(self):
        tables=connection.introspection.table_names()
        self.assertIn('game_members',tables)
        with connection.cursor() as cursor:
            member_columns = {column.name for column in connection.introspection.get_table_description(cursor, 'game_members')}
        self.assertTrue({'member_id', 'external_member_key', 'nickname', 'data_source', 'registered_at'} <= member_columns)
        for model in LOG_MODELS:
            self.assertNotIn(model._meta.db_table,tables)
        self.assertEqual(collection(PlaySession).count_documents({}),1)
        self.assertEqual(Player.objects.count(),1)

    def test_metrics_pages_charts_export_and_filters(self):
        self.solve()
        result=self.client.get('/api/admin/summary').json()
        self.assertEqual(result['summary']['success_rate'],100)
        self.assertEqual(result['learning']['completed'],1)
        self.assertEqual(result['learning']['avg_active_seconds'],30)
        for path in ['/staff/','/staff/?scope=game&topic=stack','/staff/?scope=player',
                     '/staff/?scope=player&player_id='+str(self.member.pk),'/staff/players/',
                     '/staff/players/'+str(self.member.pk)+'/', '/staff/events/', '/staff/guide/']:
            self.assertEqual(self.client.get(path, follow=True).status_code,200,path)
        visuals=self.client.get('/api/admin/visuals').json()
        self.assertEqual(visuals['runs'],1)
        self.assertEqual(len(visuals['heatmap']),168)
        self.assertEqual(self.client.get('/api/admin/events?event_type=operation_succeeded').json()['count'],1)
        self.assertEqual(self.client.get('/api/admin/events?page=999').status_code,200)
        self.assertEqual(self.client.get('/api/admin/summary?topic=queue').json()['learning']['runs'],0)
        self.assertEqual(self.client.get('/api/admin/summary?source=demo').json()['summary']['total'],0)
        self.assertEqual(self.client.get('/api/admin/summary?task_id=other').json()['summary']['sessions'],0)
        self.assertEqual(self.client.get('/api/admin/summary?start=invalid').status_code,400)
        csv=self.client.get('/staff/export/').content.decode('utf-8-sig')
        self.assertEqual(len(csv.strip().splitlines()),2)
        self.assertIn('stack-01',csv)

    def test_catalog_filters_preserve_runs_events_and_exports(self):
        from .catalog import CATALOG, AREAS, game_for
        self.assertEqual(len(CATALOG), 24)
        self.assertEqual([sum(g['area'] == a for g in CATALOG.values()) for a, _ in AREAS], [10, 6, 4, 4])
        self.assertEqual(game_for('st06')['area'], 'algorithms')
        self.assertEqual(game_for('DS09')['area'], 'structures')
        self.assertIsNone(game_for('stack-pop-test'))
        self.assertIsNone(game_for('ST03-extra'))
        # Even a legacy tree topic must not override the actual execution ID.
        collection(LearningTask).update_one({'_id': str(self.problem.pk)}, {'$set': {'task_id': 'st06'}})
        self.solve()
        other_session = create_record(PlaySession(player=self.member, topic='stack', started_at=self.now, status='in_progress'))[0]
        other_problem = create_record(LearningTask(task_id='SQL01', content_version='1', title='SQL', topic='stack'))[0]
        other_run = create_record(TaskRun(session=other_session, task=other_problem, started_at=self.now, status='in_progress'))[0]
        other_attempt = create_record(SolveAttempt(run=other_run, number=1, started_at=self.now, outcome='in_progress'))[0]
        record_event(id=uuid.uuid4(), session=other_session, run=other_run, attempt=other_attempt,
                     sequence=6, event_type='operation_succeeded', operation='select', occurred_at=self.now+timedelta(seconds=10))
        result = self.client.get('/api/admin/summary?category=algorithms').json()
        self.assertEqual(result['learning']['runs'], 1)
        self.assertEqual(result['learning']['completed'], 1)
        self.assertEqual(result['summary']['total'], 5)
        result = self.client.get('/api/admin/summary?category=sql&game_id=SQL01').json()
        self.assertEqual(result['learning']['runs'], 1)
        self.assertEqual(result['learning']['completed'], 0)
        self.assertEqual(result['summary']['total'], 1)
        self.assertEqual(self.client.get('/api/admin/summary?category=structures').json()['learning']['runs'], 0)
        self.assertEqual(self.client.get('/api/admin/summary?category=sql&game_id=ST06').status_code, 400)
        self.assertEqual(self.client.get('/api/admin/summary?game_id=NOT_A_GAME').status_code, 400)
        self.assertEqual(self.client.get('/api/admin/summary?game_id=ST06&task_id=SQL01').json()['learning']['runs'], 0)
        text = self.client.get('/staff/export/?category=algorithms&game_id=ST06').content.decode('utf-8-sig')
        self.assertIn('st06', text)
        self.assertNotIn('SQL01', text)
        response = self.client.get('/staff/?scope=game')
        catalog = response.context['catalog']
        self.assertEqual(catalog['observed'], 2)
        self.assertEqual(catalog['totals']['in_progress'], 1)
        self.assertEqual(catalog['totals']['completion_rate'], 50)
        sql = next(g for g in catalog['games'] if g['code'] == 'SQL01')
        self.assertEqual(sql['operation_rate'], 100)
        self.assertEqual(sql['completion_rate'], 0)
        self.assertContains(response, 'data-game-code=', count=24)
        response = self.client.get('/staff/?scope=game&category=algorithms')
        self.assertContains(response, 'data-game-code=', count=6)

    def test_catalog_unknown_ids_and_missing_metrics_are_not_guessed(self):
        self.event('operation_succeeded', 1, 1, operation='pop')
        response = self.client.get('/staff/')
        catalog = response.context['catalog']
        self.assertEqual(catalog['observed'], 0)
        self.assertEqual(catalog['unmapped']['runs'], 1)
        self.assertEqual(catalog['totals']['in_progress'], 1)
        self.assertEqual(catalog['totals']['completion_rate'], 0)
        self.assertIsNone(catalog['totals']['avg_seconds'])
        self.assertContains(response, '완료·포기 판정이 아직 없습니다')
        self.assertContains(response, 'stack-01')
        result = self.client.get('/api/admin/visuals').json()
        self.assertEqual(next(t for t in result['topics'] if t['label'] == '미분류')['n'], 1)
        self.assertEqual(sum(t['n'] for t in result['topics']), 1)

    def test_navigation_separates_overview_games_and_player_detail(self):
        overview = self.client.get('/staff/')
        self.assertNotContains(overview, 'class="analysis-tabs"')
        self.assertNotContains(overview, 'data-game-code=')
        self.assertNotContains(overview, 'class="chart-more')
        self.assertContains(overview, 'aria-current="page"', count=1)
        games = self.client.get('/staff/games/')
        self.assertContains(games, 'data-game-code=', count=24)
        self.assertNotContains(games, 'primary-charts')
        self.assertContains(games, 'aria-current="page"', count=1)
        detail = self.client.get('/staff/games/?game_id=ST03')
        self.assertContains(detail, '최근 작업 복구실')
        self.assertContains(detail, 'class="chart-more')
        self.assertNotContains(detail, 'data-game-code=')
        self.assertContains(detail, 'aria-current="page"', count=1)
        self.assertRedirects(self.client.get('/staff/?scope=player'), '/staff/players/')
        self.assertRedirects(self.client.get('/staff/?scope=player&player_id=' + str(self.member.pk) + '&source=live'),
                             '/staff/players/' + str(self.member.pk) + '/?source=live')

    def test_idempotency_conflict_and_reference_validation(self):
        record_id=uuid.uuid4()
        fields=dict(id=record_id,session=self.session,run=self.run,sequence=1,event_type='paused',occurred_at=self.now)
        self.assertTrue(record_event(**fields)[1])
        self.assertFalse(record_event(**fields)[1])
        with self.assertRaises(ValidationError): record_event(**{**fields,'sequence':2})
        with self.assertRaises(ValidationError): self.event('paused',1,5)
        other_session=create_record(PlaySession(player=self.member,topic='queue',started_at=self.now,status='in_progress'))[0]
        with self.assertRaises(ValidationError):
            record_event(id=uuid.uuid4(),session=other_session,run=self.run,sequence=1,event_type='paused',occurred_at=self.now)
        with self.assertRaises(ValidationError): self.event('operation_failed',2,10,operation='pop')
        with self.assertRaises(ValidationError): self.event('hint',2,10,hint_id='help',hint_step=1,payload={'password':'secret'})

    def test_pause_calculation_and_finalization(self):
        finish_record(SolveAttempt,self.attempt.pk,'success',self.now+timedelta(seconds=10))
        self.event('paused',1,10)
        self.event('resumed',2,30)
        closed=finalize_run(self.run,'completed',self.now+timedelta(seconds=60))
        self.assertEqual((closed.active_ms,closed.paused_ms),(40000,20000))
        self.assertEqual(finalize_run(self.run,'completed',self.now+timedelta(seconds=60)).pk,self.run.pk)
        with self.assertRaises(ValidationError): self.event('paused',3,40)
        with self.assertRaises(ValidationError): finalize_run(self.run,'abandoned',self.now+timedelta(seconds=60))

    def test_legacy_event_window_and_member_without_logs(self):
        self.event('hint',1,10,hint_id='help',hint_step=1)
        Player.objects.create(external_id='no:logs',display_name='No history',source='live')
        old=self.now-timedelta(days=40)
        collection(PlaySession).update_one({'_id':str(self.session.pk)},{'$set':{'started_at':old}})
        report=self.client.get('/api/admin/summary').json()['summary']
        self.assertEqual((report['sessions'],report['total'],report['players']),(0,1,2))
        self.assertEqual(self.client.get('/api/admin/players?q=no:logs').json()['results'][0]['events'],0)

    def test_directory_sorting_and_event_time_order(self):
        first = Player.objects.create(external_id='sort:a', display_name='AAA', source='live')
        last = Player.objects.create(external_id='sort:z', display_name='ZZZ', source='live')
        self.assertEqual(self.client.get('/staff/players/?sort=name').context['rows'][0]['player'].pk, first.pk)
        self.assertEqual(self.client.get('/staff/players/?sort=name_desc').context['rows'][0]['player'].pk, last.pk)
        self.assertEqual(self.client.get('/staff/players/?sort=invalid').context['selected_sort'], 'name')
        self.event('task_started', 1, 0)
        self.event('paused', 2, 10)
        self.assertEqual(self.client.get('/staff/events/?sort=oldest').context['page'][0].sequence, 1)
        self.assertEqual(self.client.get('/staff/events/?sort=recent').context['page'][0].sequence, 2)

    @override_settings(DEBUG=True)
    def test_seed_preserves_existing_and_repeats_safely(self):
        before=collection(TaskRun).find_one({'_id':str(self.run.pk)})
        call_command('seed_observatory',players=2,visits=2,stdout=StringIO())
        counts=[collection(model).count_documents({}) for model in LOG_MODELS]
        call_command('seed_observatory',players=2,visits=2,stdout=StringIO())
        self.assertEqual(counts,[collection(model).count_documents({}) for model in LOG_MODELS])
        self.assertEqual(collection(TaskRun).find_one({'_id':str(self.run.pk)}),before)
        self.assertEqual(get_user_model().objects.count(),1)
        self.assertEqual(self.client.get('/api/admin/summary?source=demo').json()['learning']['runs'],4)

    def test_mongo_outage_is_503_and_member_login_is_independent(self):
        with patch('telemetry.mongo.database',side_effect=ServerSelectionTimeoutError('offline')):
            self.assertEqual(self.client.get('/api/admin/summary').status_code,503)
            self.assertEqual(self.client.get('/staff/').status_code,503)
            with override_settings(GAME_SERVER_API_KEY='key'):
                response=self.client.post('/api/game/player-login',json.dumps({'member_id':'new','display_name':'New'}),
                    content_type='application/json',HTTP_AUTHORIZATION='Bearer key')
                self.assertEqual(response.status_code,201)

    def test_no_admin_access_for_anonymous_game_client(self):
        client=Client(enforce_csrf_checks=True)
        self.assertEqual(client.get('/api/admin/summary').status_code,401)
        self.assertEqual(client.post('/api/game/records','{}',content_type='application/json').status_code,503)

    @override_settings(GAME_SERVER_API_KEY='game-secret')
    def test_server_ingestion_lifecycle_and_retries(self):
        client=Client(enforce_csrf_checks=True)
        def send(kind,fields,key='game-secret'):
            return client.post('/api/game/records',json.dumps({'record_type':kind,'data':fields}),
                content_type='application/json',HTTP_AUTHORIZATION='Bearer '+key)
        sid,pid,rid,aid,eid=[str(uuid.uuid4()) for _ in range(5)]
        stamp=self.now.isoformat()
        self.assertEqual(send('session',{'id':sid,'player_id':str(self.member.pk),'topic':'queue','started_at':stamp},key='wrong').status_code,401)
        session={'id':sid,'player_id':str(self.member.pk),'topic':'queue','started_at':stamp}
        self.assertEqual(send('session',session).status_code,201)
        self.assertEqual(send('session',session).status_code,200)
        self.assertEqual(send('problem',{'id':pid,'task_id':'queue-01','content_version':'1','title':'Queue','topic':'queue'}).status_code,201)
        self.assertEqual(send('run',{'id':rid,'session_id':sid,'task_id':pid,'started_at':stamp}).status_code,201)
        self.assertEqual(send('attempt',{'id':aid,'run_id':rid,'number':1,'started_at':stamp}).status_code,201)
        event={'id':eid,'session_id':sid,'run_id':rid,'attempt_id':aid,'sequence':1,'event_type':'operation_succeeded','operation':'dequeue','occurred_at':stamp}
        self.assertEqual(send('event',event).status_code,201)
        self.assertEqual(send('event',event).status_code,200)
        end=(self.now+timedelta(seconds=5)).isoformat()
        self.assertEqual(send('end_attempt',{'id':aid,'status':'success','ended_at':end}).status_code,200)
        self.assertEqual(send('end_run',{'id':rid,'status':'completed','ended_at':end}).status_code,200)
        self.assertEqual(send('end_session',{'id':sid,'status':'completed','ended_at':end}).status_code,200)
        self.assertEqual(collection(TaskRun).find_one({'_id':rid})['active_ms'],5000)
        self.assertNotIn('sessionid',client.cookies)

    def test_legacy_member_migration_still_preserves_accounts(self):
        user=get_user_model().objects.create_user('legacy',role='learner',display_name='Legacy')
        module=importlib.import_module('telemetry.migrations.0002_preserve_legacy_players')
        module.preserve_players(apps,SimpleNamespace(connection=connection))
        self.assertEqual(Player.objects.get(pk=user.pk).display_name,'Legacy')
        self.assertTrue(get_user_model().objects.filter(pk=user.pk).exists())
