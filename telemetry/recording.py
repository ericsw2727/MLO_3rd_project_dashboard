"""Trusted server-side write services; deliberately not exposed as public ingestion APIs."""
from django.core.exceptions import ValidationError
from django.db import transaction
from .models import BehaviorEvent, TaskRun
import json


def validate_metadata(value):
    if len(json.dumps(value, ensure_ascii=False).encode('utf-8')) > 16384:
        raise ValidationError('상태·추가 데이터는 각각 16KB 이하여야 합니다.')
    forbidden = {'password', 'password_hash', 'authorization', 'session_cookie', 'secret_key', 'admin_registration_code'}
    def walk(item):
        if isinstance(item, dict):
            if any(str(key).lower() in forbidden for key in item):
                raise ValidationError('비밀값을 행동 로그에 저장할 수 없습니다.')
            for nested in item.values():
                walk(nested)
        elif isinstance(item, list):
            for nested in item:
                walk(nested)
    walk(value)


@transaction.atomic
def record_event(**fields):
    session = fields['session']
    type(session).objects.select_for_update().get(pk=session.pk)
    event = BehaviorEvent(**fields)
    for value in (event.state_before, event.state_after, event.payload):
        validate_metadata(value)
    existing = BehaviorEvent.objects.filter(pk=event.pk).first()
    if existing:
        keys = ['session_id', 'run_id', 'attempt_id', 'sequence', 'event_type', 'occurred_at', 'operation',
                'failure_reason', 'state_before', 'state_after', 'hint_id', 'hint_step', 'payload']
        if any(getattr(existing, k) != getattr(event, k) for k in keys):
            raise ValidationError('동일 이벤트 ID의 내용이 기존 기록과 다릅니다.')
        return existing, False
    if event.run_id:
        event.run = TaskRun.objects.select_for_update().get(pk=event.run_id)
        if event.run.ended_at:
            raise ValidationError('종료된 문제에는 새 이벤트를 추가할 수 없습니다.')
    event.full_clean()
    if event.occurred_at < session.started_at or (session.ended_at and event.occurred_at > session.ended_at):
        raise ValidationError('이벤트 시각이 세션 범위 밖입니다.')
    if event.run_id and (event.occurred_at < event.run.started_at or (event.run.ended_at and event.occurred_at > event.run.ended_at)):
        raise ValidationError('이벤트 시각이 문제 실행 범위 밖입니다.')
    event.save()
    return event, True


@transaction.atomic
def finalize_run(run, status, ended_at):
    run = TaskRun.objects.select_for_update().get(pk=run.pk)
    if status not in ('completed', 'abandoned') or ended_at < run.started_at:
        raise ValidationError('문제 종료 상태 또는 시각이 올바르지 않습니다.')
    if run.ended_at:
        if run.ended_at == ended_at and run.status == status:
            return run
        raise ValidationError('이미 종료한 문제를 덮어쓸 수 없습니다.')
    if status == 'completed' and not run.attempts.filter(outcome='success').exists():
        raise ValidationError('문제 해결에는 성공한 풀이 시도가 필요합니다.')
    paused_at = None
    paused_ms = 0
    for event in run.events.order_by('occurred_at', 'sequence'):
        if not run.started_at <= event.occurred_at <= ended_at:
            raise ValidationError('문제 범위 밖 이벤트가 있습니다.')
        if event.event_type == 'paused':
            if paused_at is not None:
                raise ValidationError('중복 일시정지 이벤트입니다.')
            paused_at = event.occurred_at
        elif event.event_type == 'resumed':
            if paused_at is None:
                raise ValidationError('일시정지 없이 재개할 수 없습니다.')
            paused_ms += int((event.occurred_at - paused_at).total_seconds()*1000)
            paused_at = None
    if paused_at is not None:
        paused_ms += int((ended_at-paused_at).total_seconds()*1000)
    elapsed_ms = int((ended_at-run.started_at).total_seconds()*1000)
    run.status, run.ended_at = status, ended_at
    run.paused_ms, run.active_ms = paused_ms, elapsed_ms-paused_ms
    run.full_clean()
    run.save(update_fields=['status', 'ended_at', 'paused_ms', 'active_ms'])
    return run
