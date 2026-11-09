"""Stable synthetic fixtures for dashboard exploration, never login accounts."""
import random
from datetime import timedelta
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from telemetry.models import Player, PlaySession, LearningTask, TaskRun, SolveAttempt, BehaviorEvent
from .seed_analytics_demo import stable


class Command(BaseCommand):
    help = 'Add 36 synthetic players and 504 varied problem runs across 28 days. Re-running preserves history.'

    def add_arguments(self, parser):
        parser.add_argument('--players',type=int,default=36)
        parser.add_argument('--visits',type=int,default=14)

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError('DEBUG=True인 로컬에서만 생성할 수 있습니다.')
        if not 1 <= options['players'] <= 100 or not 1 <= options['visits'] <= 28:
            raise CommandError('players는 1~100, visits는 1~28이어야 합니다.')
        names = ['루나', '네오', '아리', '리오', '노아', '유니', '솔', '코코', '나루', '모아', '루트', '픽셀']
        today = timezone.localtime().replace(hour=0, minute=0, second=0, microsecond=0)
        totals = {'players': 0, 'runs': 0, 'events': 0}
        with transaction.atomic():
            for index in range(options['players']):
                player, created = Player.objects.get_or_create(external_id=f'demo:observatory:v1:{index:02d}', defaults={
                    'id': stable(f'observatory:player:{index}'), 'display_name': f'{names[index%12]} {index+1:02d}', 'source': 'demo'})
                if player.source != 'demo':
                    raise CommandError('데모 식별자가 실제 플레이어와 충돌합니다.')
                totals['players'] += int(created)
                for visit in range(options['visits']):
                    key = f'observatory:v1:{index}:{visit}'
                    if TaskRun.objects.filter(pk=stable(key)).exists():
                        continue
                    rng = random.Random(12000 + index*97 + visit)
                    topic, label = PlaySession.TOPICS[(index+visit)%3]
                    level = 1 + rng.randrange(3)
                    version = '1.1' if rng.random() < .52 else '1.0'
                    task, _ = LearningTask.objects.get_or_create(task_id=f'{topic}-{level:02d}', content_version=version,
                        defaults={'id': stable(f'observatory:task:{topic}:{level}:{version}'), 'title': f'{label} {level}단계 연산 탐험', 'topic': topic})
                    # Complete days only: no future events, and deterministic relative-day distribution.
                    start = today - timedelta(days=1+(visit*2+index%3)%27) + timedelta(hours=rng.choice([8,10,12,14,16,18,19,20,21,22]),minutes=rng.randrange(60))
                    skill = .40 + (index%6)*.07
                    probability = skill + (.09 if version=='1.1' else 0) - .08*(level-1)
                    draw = rng.random()
                    status = 'completed' if draw < probability else 'in_progress' if draw > .93 else 'abandoned'
                    attempt_count = rng.choices([1,2,3,4],[4 if index%6>3 else 1,4,3,2])[0]
                    session = PlaySession(id=stable(key+':session'),player=player,topic=topic,level=level,game_version='synthetic-observatory-1.0',started_at=start,status='in_progress')
                    session.save()
                    run = TaskRun.objects.create(id=stable(key),session=session,task=task,started_at=start,status='in_progress')
                    events=[];attempts=[];seconds=0;paused=0
                    def emit(kind, attempt=None, **fields):
                        events.append(BehaviorEvent(id=stable(key+f':event:{len(events)+1}'),session=session,run=run,attempt=attempt,
                            sequence=len(events)+1,event_type=kind,occurred_at=start+timedelta(seconds=seconds),
                            payload={'synthetic': True, 'dataset': 'observatory-v1', 'schema_version': '2.0'},**fields))
                    emit('task_started')
                    for number in range(1,attempt_count+1):
                        seconds+=rng.randint(2,6)
                        last=number==attempt_count
                        outcome='success' if last and status=='completed' else 'in_progress' if last and status=='in_progress' else 'failure'
                        attempt=SolveAttempt(id=stable(key+f':attempt:{number}'),run=run,number=number,
                            started_at=start+timedelta(seconds=seconds),outcome=outcome)
                        emit('attempt_started',attempt)
                        seconds+=rng.randint(8,28)+level*6+(5-index%6)*3
                        op={'stack':rng.choice(['push','pop']), 'queue':rng.choice(['enqueue','dequeue']), 'tree':rng.choice(['select_node','insert'])}[topic]
                        reason=rng.choice({'stack':['empty_stack','wrong_order','wrong_target'], 'queue':['wrong_order','empty_queue','capacity_exceeded'], 'tree':['wrong_node','wrong_branch','wrong_order']}[topic])
                        emit('operation_succeeded' if outcome=='success' else 'operation_failed',attempt,operation=op,
                             failure_reason='' if outcome=='success' else reason,state_before={'size':rng.randrange(4)},state_after={'size':rng.randrange(4)})
                        if outcome!='in_progress':
                            seconds+=2
                            attempt.ended_at=start+timedelta(seconds=seconds)
                            emit('attempt_succeeded' if outcome=='success' else 'attempt_failed',attempt)
                        attempts.append(attempt)
                        if outcome!='success' and rng.random()<.67:
                            seconds+=3;emit('hint',hint_id=f'{topic}-guide-{level}',hint_step=rng.randint(1,3))
                        if not last and rng.random()<.3:
                            seconds+=1;emit('paused');pause=rng.randint(15,75);seconds+=pause;paused+=pause;emit('resumed')
                    seconds+=3
                    if status!='in_progress':
                        emit('task_completed' if status=='completed' else 'task_abandoned')
                        run.ended_at=start+timedelta(seconds=seconds);run.active_ms=(seconds-paused)*1000;run.paused_ms=paused*1000
                        session.ended_at=run.ended_at;session.duration_ms=seconds*1000
                    run.status=status;session.status=status
                    run.full_clean();run.save();session.save()
                    SolveAttempt.objects.bulk_create(attempts)
                    for event in events:
                        event.clean()
                    BehaviorEvent.objects.bulk_create(events,batch_size=500)
                    totals['runs']+=1;totals['events']+=len(events)
        self.stdout.write(self.style.SUCCESS(f'Observatory demo created: {totals}. Existing records unchanged.'))
