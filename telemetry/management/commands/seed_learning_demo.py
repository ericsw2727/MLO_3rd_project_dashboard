from datetime import timedelta
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from telemetry.models import Player, PlaySession, LearningTask, TaskRun, SolveAttempt, BehaviorEvent
from telemetry.recording import record_event, finalize_run
from .seed_analytics_demo import stable


class Command(BaseCommand):
    help = 'Add structured problem/attempt/operation demo history; preserve all existing data.'

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError('DEBUG=True인 로컬에서만 생성할 수 있습니다.')
        created = 0
        with transaction.atomic():
            for index in range(6):
                player, _ = Player.objects.get_or_create(external_id=f'demo:analytics:{index}', defaults={
                    'id': stable(f'player:{index}'), 'display_name': f'데모 탐험가 {index+1}', 'source': 'demo'})
                if player.source != 'demo':
                    raise CommandError('실제 출처 플레이어에는 데모를 추가할 수 없습니다.')
                for topic_index, (topic, label) in enumerate(PlaySession.TOPICS):
                    key = f'learning-v2:{index}:{topic}'
                    if TaskRun.objects.filter(pk=stable(key)).exists():
                        continue
                    version = '1.0' if index % 2 == 0 else '1.1'
                    task, _ = LearningTask.objects.get_or_create(task_id=f'{topic}-03', content_version=version, defaults={
                        'id': stable(f'task:{topic}:{version}'), 'title': f'{label} 연산 순서 이해', 'topic': topic})
                    start = timezone.now().replace(microsecond=0) - timedelta(hours=2, days=topic_index, minutes=index*5)
                    mode = (index + topic_index) % 3
                    duration = 25 if mode == 0 else 80
                    session = PlaySession.objects.create(id=stable(key+':session'), player=player, topic=topic,
                        game_version='synthetic-2.0', level=3, started_at=start,
                        ended_at=start+timedelta(seconds=duration+5), status='completed' if mode != 2 else 'abandoned',
                        duration_ms=(duration+5)*1000)
                    run = TaskRun.objects.create(id=stable(key), session=session, task=task, started_at=start, status='in_progress')
                    attempt1 = SolveAttempt.objects.create(id=stable(key+':attempt:1'), run=run, number=1,
                        started_at=start+timedelta(seconds=5), ended_at=start+timedelta(seconds=20),
                        outcome='success' if mode==0 else 'failure')
                    operation = {'stack': 'pop', 'queue': 'dequeue', 'tree': 'select_node'}[topic]
                    reason = {'stack': 'empty_stack', 'queue': 'wrong_order', 'tree': 'wrong_node'}[topic]
                    def event(sec, kind, attempt=None, **extra):
                        return (sec, kind, attempt, extra)
                    schedule = [event(0,'task_started'), event(5,'attempt_started',attempt1)]
                    if mode == 0:
                        schedule += [event(15,'operation_succeeded',attempt1,operation=operation,state_before={'size':2},state_after={'size':1}),
                                     event(20,'attempt_succeeded',attempt1),event(25,'task_completed')]
                    else:
                        attempt2 = SolveAttempt.objects.create(id=stable(key+':attempt:2'),run=run,number=2,
                            started_at=start+timedelta(seconds=50),ended_at=start+timedelta(seconds=75),
                            outcome='success' if mode==1 else 'failure')
                        schedule += [event(15,'operation_failed',attempt1,operation=operation,failure_reason=reason,
                                           state_before={'size':0,'selected_node':'B'},state_after={'size':0,'selected_node':'B'}),
                                     event(20,'attempt_failed',attempt1),event(22,'hint',hint_id=f'{topic}-guide-1',hint_step=1),
                                     event(25,'paused'),event(45,'resumed'),event(50,'attempt_started',attempt2),
                                     event(70,'operation_succeeded' if mode==1 else 'operation_failed',attempt2,operation=operation,
                                           failure_reason='' if mode==1 else reason,state_before={'size':1},state_after={'size':0}),
                                     event(75,'attempt_succeeded' if mode==1 else 'attempt_failed',attempt2),
                                     event(80,'task_completed' if mode==1 else 'task_abandoned')]
                    for sequence, (seconds, kind, attempt, extra) in enumerate(schedule,1):
                        record_event(id=stable(key+f':event:{sequence}'),session=session,run=run,attempt=attempt,
                            sequence=sequence,event_type=kind,occurred_at=start+timedelta(seconds=seconds),
                            payload={'synthetic':True,'schema_version':'2.0'},**extra)
                    finalize_run(run,'completed' if mode!=2 else 'abandoned',start+timedelta(seconds=duration))
                    created += 1
        self.stdout.write(self.style.SUCCESS(f'Created {created} structured problem runs. Existing history preserved.'))
