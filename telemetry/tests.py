import importlib
from datetime import timedelta
from io import StringIO
from types import SimpleNamespace
from django.apps import apps
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db import IntegrityError, transaction, connection
from django.test import TestCase, override_settings
from django.utils import timezone
from .models import Player, PlaySession, BehaviorEvent


class AnalyticsTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_user('admin', password='Admin-Only!4972', display_name='운영자')
        self.client.force_login(self.admin)
        self.player = Player.objects.create(external_id='device:one', display_name='플레이어 A', source='live')
        self.demo = Player.objects.create(external_id='demo:one', display_name='데모 플레이어', source='demo')
        self.now = timezone.now()
        self.session = PlaySession.objects.create(player=self.player, topic='stack', level=1, started_at=self.now,
            ended_at=self.now+timedelta(seconds=60), duration_ms=60000, status='completed')
        for seq, kind in enumerate(['attempt', 'failure', 'hint', 'attempt', 'success'], 1):
            BehaviorEvent.objects.create(session=self.session, sequence=seq, event_type=kind, occurred_at=self.now)
        demo_session = PlaySession.objects.create(player=self.demo, topic='queue', started_at=self.now, status='abandoned')
        BehaviorEvent.objects.create(session=demo_session, sequence=1, event_type='failure', occurred_at=self.now)

    def test_dashboard_analysis_scopes(self):
        overview = self.client.get('/staff/')
        self.assertContains(overview, '전체 종합')
        self.assertEqual(len(overview.context['game_rows']), 3)
        game = self.client.get('/staff/', {'scope': 'game', 'topic': 'stack'})
        self.assertEqual(game.context['stats']['total'], 5)
        self.assertEqual(game.context['game_rows'][1]['stats']['total'], 1)
        listing = self.client.get('/staff/', {'scope': 'player'})
        self.assertFalse(listing.context['show_analysis'])
        selected = self.client.get('/staff/', {'scope': 'player', 'player_id': str(self.player.pk)})
        self.assertTrue(selected.context['show_analysis'])
        self.assertEqual(selected.context['stats']['total'], 5)
        self.assertEqual(selected.context['learning']['runs'], 0)
        invalid = self.client.get('/api/admin/summary', {'player_id': 'invalid'})
        self.assertEqual(invalid.status_code, 400)

    def test_summary_metrics_and_source_isolation(self):
        response = self.client.get('/api/admin/summary?source=live')
        self.assertEqual(response.status_code, 200)
        stats = response.json()['summary']
        self.assertEqual((stats['players'],stats['sessions'],stats['total']), (1,1,5))
        self.assertEqual((stats['success_rate'],stats['hints'],stats['avg_seconds']), (50,1,60))
        self.assertEqual(self.client.get('/api/admin/summary?source=demo').json()['summary']['success_rate'],0)
        self.assertEqual(self.client.get('/api/admin/summary?topic=tree').json()['summary']['success_rate'],None)
        self.assertEqual(self.client.get('/api/admin/summary?source=live&event_type=hint').json()['summary']['total'],5)

    def test_search_player_detail_and_no_auth_secrets(self):
        response = self.client.get('/api/admin/players?q=device:one')
        self.assertEqual(response.json()['count'],1)
        self.assertEqual(response.json()['results'][0]['sessions'],1)
        detail = self.client.get(f'/api/admin/players/{self.player.pk}').json()
        self.assertEqual(detail['summary']['total'],5)
        self.assertNotIn('password', str(detail))
        self.assertNotIn('login_id', str(detail))
        self.assertEqual(self.client.get('/api/admin/players/00000000-0000-0000-0000-000000000000').status_code,404)

    def test_event_filter_pagination_and_invalid_filters(self):
        result = self.client.get('/api/admin/events?source=live&event_type=hint').json()
        self.assertEqual(result['count'],1)
        self.assertEqual(result['results'][0]['event_type'],'hint')
        for query in ['start=invalid','start=2026-11-05&end=2020-01-01','source=bad','topic=bad','end=9999-12-31']:
            self.assertEqual(self.client.get('/api/admin/summary?'+query).status_code,400)
        self.assertEqual(self.client.get('/api/admin/events?page=999').status_code,200)

    def test_date_window_uses_event_time_and_session_start(self):
        old = self.now-timedelta(days=30)
        PlaySession.objects.filter(pk=self.session.pk).update(started_at=old)
        stats = self.client.get('/api/admin/summary?source=live').json()['summary']
        self.assertEqual(stats['sessions'],0)
        self.assertEqual(stats['total'],5)

    def test_html_views(self):
        for path in ['/','/staff/','/staff/players/','/staff/events/',f'/staff/players/{self.player.pk}/','/me/']:
            self.assertEqual(self.client.get(path).status_code,200)
        self.assertContains(self.client.get('/staff/players/'),'플레이어 A')
        self.assertContains(self.client.get('/staff/events/?event_type=hint'),'힌트')
        self.assertContains(self.client.get('/staff/?start=invalid'),'올바른')

    def test_database_constraints(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            BehaviorEvent.objects.create(session=self.session,sequence=1,event_type='success',occurred_at=self.now)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Player.objects.create(external_id='device:one',display_name='duplicate')
        with self.assertRaises(IntegrityError), transaction.atomic():
            BehaviorEvent.objects.create(session=self.session,sequence=99,event_type='unknown',occurred_at=self.now)

    @override_settings(DEBUG=True)
    def test_demo_seed_idempotent_and_no_login_accounts(self):
        before = get_user_model().objects.count()
        call_command('seed_analytics_demo',stdout=StringIO())
        sizes = (Player.objects.count(),PlaySession.objects.count(),BehaviorEvent.objects.count())
        call_command('seed_analytics_demo',stdout=StringIO())
        self.assertEqual(sizes,(Player.objects.count(),PlaySession.objects.count(),BehaviorEvent.objects.count()))
        self.assertEqual(before,get_user_model().objects.count())
        self.assertEqual(PlaySession.objects.filter(player__source='demo').count(),37)

    def test_legacy_migration_preserves_id_and_account(self):
        user = get_user_model().objects.create_user('legacy',display_name='기존 학습자',role='learner')
        module = importlib.import_module('telemetry.migrations.0002_preserve_legacy_players')
        module.preserve_players(apps,SimpleNamespace(connection=connection))
        player = Player.objects.get(pk=user.pk)
        self.assertEqual(player.display_name,'기존 학습자')
        self.assertTrue(get_user_model().objects.filter(pk=user.pk,role='learner').exists())
        module.preserve_players(apps,SimpleNamespace(connection=connection))
        self.assertEqual(Player.objects.filter(pk=user.pk).count(),1)


class StructuredLearningTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        with override_settings(DEBUG=True):
            call_command('seed_learning_demo', stdout=StringIO())
        cls.admin = get_user_model().objects.create_user('analysis-admin',password='Admin-Only!4972')

    def setUp(self):
        self.client.force_login(self.admin)

    def test_known_problem_metrics_versions_and_hint_denominator(self):
        data = self.client.get('/api/admin/summary?source=demo').json()['learning']
        self.assertEqual(data['runs'],18)
        self.assertEqual(data['completed'],12)
        self.assertEqual(data['abandoned'],6)
        self.assertEqual(data['completion_rate'],66.7)
        self.assertEqual(data['retry_runs'],12)
        self.assertEqual(data['hint_evaluable'],12)
        self.assertEqual(data['hint_next_success'],6)
        self.assertEqual(data['avg_active_seconds'],42.5)
        self.assertEqual(len(data['tasks']),6)
        self.assertEqual(self.client.get('/api/admin/summary?task_id=stack-03&content_version=1.0').json()['learning']['runs'],3)
        self.assertEqual(self.client.get('/api/admin/summary?source=live').json()['learning']['runs'],0)

    @override_settings(DEBUG=True)
    def test_new_seed_preserves_data_and_does_not_duplicate(self):
        from .models import TaskRun,SolveAttempt,LearningTask
        before=(Player.objects.count(),PlaySession.objects.count(),BehaviorEvent.objects.count(),TaskRun.objects.count(),SolveAttempt.objects.count(),LearningTask.objects.count())
        call_command('seed_learning_demo',stdout=StringIO())
        self.assertEqual(before,(Player.objects.count(),PlaySession.objects.count(),BehaviorEvent.objects.count(),TaskRun.objects.count(),SolveAttempt.objects.count(),LearningTask.objects.count()))

    def test_rich_log_and_pages(self):
        data=self.client.get('/api/admin/events?event_type=operation_failed').json()
        self.assertEqual(data['count'],18)
        event=data['results'][0]
        self.assertTrue(event['task_id'])
        self.assertTrue(event['attempt_id'])
        self.assertTrue(event['failure_reason'])
        self.assertEqual(self.client.get('/staff/').status_code,200)
        self.assertContains(self.client.get('/staff/'),'문제 풀이 분석')
        self.assertContains(self.client.get('/staff/events/?task_id=stack-03'),'stack-03')
        player=Player.objects.filter(source='demo').first()
        self.assertContains(self.client.get(f'/staff/players/{player.pk}/'),'문제 풀이 분석')

    def test_validation_replay_cross_links_and_finalization(self):
        import uuid
        from django.core.exceptions import ValidationError
        from .models import TaskRun,LearningTask,SolveAttempt
        from .recording import record_event,finalize_run
        player=Player.objects.first()
        now=timezone.now()-timedelta(minutes=5)
        session=PlaySession.objects.create(player=player,topic='stack',started_at=now,status='in_progress')
        task=LearningTask.objects.get(task_id='stack-03',content_version='1.0')
        run=TaskRun.objects.create(session=session,task=task,started_at=now,status='in_progress')
        SolveAttempt.objects.create(run=run,number=1,started_at=now,outcome='success')
        event_id=uuid.uuid4()
        fields={'id':event_id,'session':session,'run':run,'sequence':1,'event_type':'paused','occurred_at':now+timedelta(seconds=10)}
        self.assertTrue(record_event(**fields)[1])
        self.assertFalse(record_event(**fields)[1])
        with self.assertRaises(ValidationError):
            record_event(**{**fields,'sequence':2})
        record_event(id=uuid.uuid4(),session=session,run=run,sequence=2,event_type='resumed',occurred_at=now+timedelta(seconds=30))
        closed=finalize_run(run,'completed',now+timedelta(seconds=60))
        self.assertEqual((closed.active_ms,closed.paused_ms),(40000,20000))
        self.assertFalse(record_event(**fields)[1])
        with self.assertRaises(ValidationError):
            record_event(id=uuid.uuid4(),session=session,run=run,sequence=3,event_type='hint',hint_id='x',hint_step=1,occurred_at=now+timedelta(seconds=40))
        other=TaskRun.objects.exclude(pk=run.pk).first()
        invalid=BehaviorEvent(session=session,run=other,sequence=7,event_type='task_started',occurred_at=now)
        with self.assertRaises(ValidationError): invalid.full_clean()
        timed = BehaviorEvent.objects.filter(attempt__isnull=False).first()
        timed.occurred_at = timed.attempt.started_at-timedelta(seconds=1)
        with self.assertRaises(ValidationError): timed.full_clean()


    def test_sensitive_metadata_is_rejected(self):
        from django.core.exceptions import ValidationError
        from .recording import validate_metadata
        with self.assertRaises(ValidationError): validate_metadata({'nested': {'password': 'do-not-store'}})
        with self.assertRaises(ValidationError): validate_metadata({'large': 'x'*17000})
        validate_metadata({'stack_size': 3})


class VisualizationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        with override_settings(DEBUG=True):
            call_command('seed_observatory',players=2,visits=3,stdout=StringIO())
        cls.admin=get_user_model().objects.create_user('visual-admin',password='Visual-Admin!4972')

    def setUp(self):
        self.client.force_login(self.admin)

    def test_filter_scope_chart_totals_and_empty_state(self):
        data=self.client.get('/api/admin/visuals?source=demo').json()
        self.assertEqual(data['runs'],6)
        self.assertEqual(sum(r['value'] for r in data['outcomes']),6)
        self.assertEqual(sum(r['started'] for r in data['trend']),6)
        self.assertEqual(sum(r['value'] for r in data['attempts']),6)
        self.assertEqual(sum(r['value'] for r in data['histogram']),sum(1 for r in __import__('telemetry.models',fromlist=['TaskRun']).TaskRun.objects.filter(status='completed')))
        self.assertEqual(len(data['heatmap']),168)
        empty=self.client.get('/api/admin/visuals?source=live').json()
        self.assertTrue(empty['empty'])
        self.assertEqual(empty['quality']['events'],0)
        self.assertEqual(self.client.get('/api/admin/visuals?topic=invalid').status_code,400)
        player=Player.objects.first()
        scoped=self.client.get('/api/admin/visuals?q='+player.external_id).json()
        self.assertEqual(scoped['runs'],3)

    @override_settings(DEBUG=True)
    def test_seed_idempotence_and_existing_history(self):
        from .models import TaskRun,SolveAttempt
        sizes=(Player.objects.count(),PlaySession.objects.count(),TaskRun.objects.count(),SolveAttempt.objects.count(),BehaviorEvent.objects.count())
        ids=set(BehaviorEvent.objects.values_list('pk',flat=True))
        call_command('seed_observatory',players=2,visits=3,stdout=StringIO())
        self.assertEqual(sizes,(Player.objects.count(),PlaySession.objects.count(),TaskRun.objects.count(),SolveAttempt.objects.count(),BehaviorEvent.objects.count()))
        self.assertEqual(ids,set(BehaviorEvent.objects.values_list('pk',flat=True)))
        self.assertFalse(Player.objects.filter(source='live').exists())
        self.assertEqual(get_user_model().objects.count(),1)
        for event in BehaviorEvent.objects.select_related('attempt','run','session'):
            event.clean()

    def test_dashboard_assets_export_and_authorization(self):
        response=self.client.get('/staff/')
        self.assertContains(response,'data-chart=',count=10)
        self.assertContains(response,'visualization-data')
        self.assertContains(response,'/static/js/observatory.js')
        self.assertEqual(self.client.get('/staff/guide/').status_code,200)
        csv=self.client.get('/staff/export/?source=demo')
        self.assertEqual(csv.status_code,200)
        self.assertEqual(len(csv.content.decode('utf-8-sig').strip().splitlines()),7)
        self.assertEqual(self.client.get('/staff/export/?source=live').content.decode('utf-8-sig').strip().count('\n'),0)
        self.client.logout()
        self.assertEqual(self.client.get('/api/admin/visuals').status_code,401)
        self.assertRedirects(self.client.get('/staff/export/'),'/staff/login/')
