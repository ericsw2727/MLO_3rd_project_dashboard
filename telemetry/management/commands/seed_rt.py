"""Mock rt_* documents in the common-contract shape.

Use until the pipeline writes real data. Every mock document carries
mock=True, so `seed_rt --clear` removes only mock rows and never touches
documents written by Spark.
"""
import random
from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from telemetry.catalog import CATALOG, CATEGORY_AREAS
from telemetry.mongo import database

AREA_CATEGORY = {area: code for code, area in CATEGORY_AREAS.items()}
COLLECTIONS = ('rt_minigame_1m', 'rt_alerts', 'rt_summary', 'rt_updates', 'rt_versions')


class Command(BaseCommand):
    help = 'rt_* 컬렉션에 공통 계약 형식의 목업 데이터를 넣습니다 (--clear로 목업만 삭제).'

    def add_arguments(self, parser):
        parser.add_argument('--clear', action='store_true', help='mock=True 문서만 삭제')
        parser.add_argument('--minutes', type=int, default=60, help='채울 과거 분 수 (기본 60)')

    def handle(self, *args, **options):
        if not settings.DEBUG and not options['clear']:
            raise CommandError('목업 생성은 DJANGO_DEBUG=True 환경에서만 실행합니다.')
        db = database()
        if options['clear']:
            for name in COLLECTIONS:
                removed = db[name].delete_many({'mock': True}).deleted_count
                self.stdout.write(f'{name}: 목업 {removed}건 삭제')
            return
        rng = random.Random(20261120)
        now = timezone.now().replace(second=0, microsecond=0)
        minutes = max(1, min(options['minutes'], 180))
        hot = {'ST04', 'SQL03'}  # failure spikes for the alert list
        for code, game in CATALOG.items():
            category = AREA_CATEGORY[game['area']]
            base = rng.uniform(0.45, 0.85)
            for offset in range(minutes, 0, -1):
                start = now - timedelta(minutes=offset)
                attempts = rng.randint(0, 9)
                rate = base - (0.35 if code in hot and offset < 12 else 0) + rng.uniform(-0.1, 0.1)
                successes = min(attempts, max(0, round(attempts * rate)))
                doc = {'window_start': start, 'window_end': start + timedelta(minutes=1), 'minigame_id': code,
                       'category': category, 'attempts': attempts, 'successes': successes,
                       'failures': attempts - successes, 'hints': rng.randint(0, 2), 'players': max(1, attempts // 2),
                       'success_rate': round(successes / attempts, 3) if attempts else None,
                       'updated_at': now, 'mock': True}
                db.rt_minigame_1m.replace_one({'_id': f'{code}:{start.isoformat()}'}, doc, upsert=True)
            for offset in range(min(minutes, 60), 0, -1):
                start = now - timedelta(minutes=offset + 4)
                spike = code in hot and offset < 10
                attempts = rng.randint(25, 40) if spike else rng.randint(5, 30)
                failures = round(attempts * (rng.uniform(0.5, 0.7) if spike else rng.uniform(0.1, 0.35)))
                doc = {'window_start': start, 'window_end': start + timedelta(minutes=5), 'minigame_id': code,
                       'category': category, 'attempts': attempts, 'failures': failures,
                       'failure_rate': round(failures / attempts, 3), 'baseline_rate': 0.25,
                       'alert': spike and attempts >= 20 and failures / attempts >= 0.4, 'updated_at': now, 'mock': True}
                db.rt_alerts.replace_one({'_id': f'{code}:{start.isoformat()}'}, doc, upsert=True)
        db.rt_summary.replace_one({'_id': 'global'}, {'events_last_1m': rng.randint(80, 220),
                                  'active_sessions_5m': rng.randint(12, 40), 'updated_at': timezone.now(), 'mock': True},
                                  upsert=True)
        target = 'content-2026.11.19'
        for offset in range(min(minutes, 60), 0, -5):
            start = now - timedelta(minutes=offset)
            started = rng.randint(3, 12)
            failed = rng.randint(0, 2) if offset > 15 else rng.randint(2, 5)
            doc = {'window_start': start, 'target_version': target, 'checks': started + rng.randint(5, 15),
                   'prompted': started + 2, 'accepted': started, 'dismissed': 2, 'downloads_started': started,
                   'downloads_succeeded': max(0, started - failed), 'downloads_failed': failed,
                   'mounted': max(0, started - failed), 'failure_rate': round(failed / started, 3) if started else 0,
                   'p50_duration_ms': rng.randint(2500, 9000),
                   'top_failure_reason': rng.choice(['network', 'hash_mismatch', 'http_error']) if failed else None,
                   'updated_at': now, 'mock': True}
            db.rt_updates.replace_one({'_id': f'{target}:{start.isoformat()}'}, doc, upsert=True)
        for kind, version, installs in [('build', '0.3.1', 41), ('build', '0.3.0', 17), ('build', '0.2.9', 4),
                                        ('content', target, 36), ('content', 'content-2026.11.12', 14), ('content', 'base', 12)]:
            total = 62
            db.rt_versions.replace_one({'_id': f'{kind}:{version}'}, {'kind': kind, 'version': version, 'installs': installs,
                                       'share': round(installs / total, 3), 'updated_at': now, 'mock': True}, upsert=True)
        self.stdout.write(self.style.SUCCESS(
            f'목업 생성: 미니게임 {len(CATALOG)}종 x {minutes}분, 경고·업데이트·버전·요약'))
