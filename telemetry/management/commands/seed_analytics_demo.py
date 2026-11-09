import uuid
from datetime import timedelta
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from telemetry.models import Player, PlaySession, BehaviorEvent

NAMESPACE = uuid.UUID('3b5d89d4-c510-4b52-aef2-9e914167941a')


def stable(value):
    return uuid.uuid5(NAMESPACE, value)


class Command(BaseCommand):
    help = 'Create deterministic, synthetic analysis fixtures. Does not create login accounts or modify existing records.'

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError('DEBUG=True 로컬 환경에서만 실행할 수 있습니다.')
        created = {'players': 0, 'sessions': 0, 'events': 0}
        anchor = timezone.now().replace(hour=1, minute=0, second=0, microsecond=0)
        with transaction.atomic():
            for index, name in enumerate(['노드 탐험가', '스택 마스터', '큐 러너', '트리 워커', '초보 탐색자', '연결 설계자']):
                player, new = Player.objects.get_or_create(external_id=f'demo:analytics:{index}', defaults={
                    'id': stable(f'player:{index}'), 'display_name': name, 'source': 'demo'})
                if player.source != 'demo' or player.pk != stable(f'player:{index}'):
                    raise CommandError('데모 식별자가 기존 데이터와 충돌합니다. 기존 데이터는 변경하지 않습니다.')
                created['players'] += int(new)
                for day in range(6):
                    topic = ['stack', 'queue', 'tree'][(index + day) % 3]
                    start = anchor - timedelta(days=day, minutes=index * 20)
                    completed = (index + day) % 4 != 0
                    duration = (120 + index * 35 + day * 12) * 1000
                    session, new = PlaySession.objects.get_or_create(id=stable(f'session:{index}:{day}'), defaults={
                        'player': player, 'topic': topic, 'level': day % 3 + 1, 'game_version': 'synthetic-1.0',
                        'started_at': start, 'ended_at': start + timedelta(milliseconds=duration),
                        'duration_ms': duration, 'status': 'completed' if completed else 'abandoned'})
                    created['sessions'] += int(new)
                    # Preserve timestamps and topic of prior seed runs. Never shift old demo history.
                    kinds = ['level_start', 'attempt', 'failure', 'hint', 'attempt', 'success'] if completed else ['level_start', 'attempt', 'failure', 'hint']
                    for sequence, kind in enumerate(kinds, 1):
                        _, new = BehaviorEvent.objects.get_or_create(session=session, sequence=sequence, defaults={
                            'id': stable(f'event:{index}:{day}:{sequence}'), 'event_type': kind,
                            'occurred_at': session.started_at + timedelta(seconds=sequence * 10),
                            'payload': {'synthetic': True, 'task_id': f'{session.topic}-{session.level:02d}'}})
                        created['events'] += int(new)
        self.stdout.write(self.style.SUCCESS(f'Synthetic demo created: {created}. Existing data unchanged.'))
