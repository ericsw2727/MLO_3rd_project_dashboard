"""Synthetic demo writes: members in MySQL, all learning data in MongoDB."""
import random
from datetime import timedelta
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from pymongo import UpdateOne
from telemetry.models import Player, PlaySession, LearningTask, TaskRun, SolveAttempt, BehaviorEvent
from telemetry.mongo import collection, document, initialize_indexes
from .seed_analytics_demo import stable


class Command(BaseCommand):
    help = 'Add synthetic MongoDB play records, preserving existing data.'

    def add_arguments(self, parser):
        parser.add_argument('--players', type=int, default=36)
        parser.add_argument('--visits', type=int, default=14)

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError('Demo generation requires DEBUG=True.')
        if not 1 <= options['players'] <= 100 or not 1 <= options['visits'] <= 28:
            raise CommandError('players: 1..100, visits: 1..28')
        initialize_indexes()
        documents = {model: {} for model in (PlaySession, LearningTask, TaskRun, SolveAttempt, BehaviorEvent)}
        def add(record):
            documents[type(record)][str(record.pk)] = document(record)
        anchor = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        for index in range(options['players']):
            member, _ = Player.objects.get_or_create(external_id=f'demo:mongo:{index}',
                defaults={'id': stable(f'mongo:member:{index}'), 'display_name': f'Demo explorer {index+1:02d}', 'source': 'demo'})
            if member.source != 'demo':
                raise CommandError('Demo identity conflicts with a live member.')
            for visit in range(options['visits']):
                key = f'mongo:visit:{index}:{visit}'
                if collection(TaskRun).find_one({'_id': str(stable(key))}):
                    continue
                rng = random.Random(12000 + index*97 + visit)
                topic = ['stack', 'queue', 'tree'][(index+visit)%3]
                version = '1.0' if index%2 else '1.1'
                start = anchor - timedelta(days=1+(visit*2+index%3)%27) + timedelta(hours=9+index%12)
                status = rng.choice(['completed', 'completed', 'abandoned', 'in_progress'])
                duration = rng.randint(30,180)
                end = start+timedelta(seconds=duration) if status != 'in_progress' else None
                problem = LearningTask(id=stable(f'mongo:problem:{topic}:{version}'), task_id=f'{topic}-01',
                    content_version=version, title=f'{topic} practice', topic=topic)
                session = PlaySession(id=stable(key+':session'), player=member, topic=topic, level=1,
                    game_version='synthetic-mongo-1.0', started_at=start, ended_at=end, status=status,
                    duration_ms=duration*1000 if end else None)
                run = TaskRun(id=stable(key), session=session, task=problem, started_at=start, ended_at=end,
                    status=status, active_ms=duration*1000 if end else None, paused_ms=0)
                for item in (problem,session,run): add(item)
                sequence=0
                def emit(kind, seconds, attempt=None, **extra):
                    nonlocal sequence
                    sequence += 1
                    add(BehaviorEvent(id=stable(key+f':event:{sequence}'), session=session, run=run, attempt=attempt,
                        sequence=sequence,event_type=kind,occurred_at=start+timedelta(seconds=seconds),
                        received_at=start+timedelta(seconds=seconds),payload={'synthetic':True},**extra))
                emit('task_started',0)
                retry = index%3 != 0
                count=2 if retry else 1
                for number in range(1,count+1):
                    seconds=2+(number-1)*(duration//2)
                    outcome='failure' if number<count or status=='abandoned' else 'success' if status=='completed' else 'in_progress'
                    attempt=SolveAttempt(id=stable(key+f':attempt:{number}'),run=run,number=number,
                        started_at=start+timedelta(seconds=seconds),
                        ended_at=start+timedelta(seconds=seconds+10) if outcome!='in_progress' else None,outcome=outcome)
                    add(attempt)
                    emit('attempt_started',seconds,attempt)
                    emit('operation_succeeded' if outcome=='success' else 'operation_failed',seconds+5,attempt,
                         operation={'stack':'pop','queue':'dequeue','tree':'select_node'}[topic],
                         failure_reason='' if outcome=='success' else 'wrong_order')
                    if outcome!='in_progress': emit('attempt_succeeded' if outcome=='success' else 'attempt_failed',seconds+10,attempt)
                    if number<count: emit('hint',seconds+11,hint_id=f'{topic}-help',hint_step=1)
                if end: emit('task_completed' if status=='completed' else 'task_abandoned',duration)
        created = 0
        for model, items in documents.items():
            if items:
                result = collection(model).bulk_write([UpdateOne({'_id':key},{'$setOnInsert':value},upsert=True)
                                                      for key,value in items.items()])
                created += result.upserted_count
        self.stdout.write(self.style.SUCCESS(f'MongoDB demo: {created} new documents. Existing records preserved.'))
