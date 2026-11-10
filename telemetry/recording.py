"""Validated MongoDB writes. SQL is used only to resolve a game member."""
import uuid
from contextlib import contextmanager
from datetime import timedelta
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Player, PlaySession, LearningTask, TaskRun, SolveAttempt, BehaviorEvent
from .metadata import validate_metadata
from .mongo import collection, document, get_record, insert_record, normalized


def finish_record(model, record_id, outcome, ended_at):
    if model not in (PlaySession, SolveAttempt):
        raise ValidationError('세션 또는 시도만 종료할 수 있습니다.')
    record = get_record(model, record_id)
    session_id = record.pk if model is PlaySession else get_record(TaskRun, record.run_id).session_id
    with session_lock(session_id):
        record = get_record(model, record_id)
        if timezone.is_naive(ended_at):
            raise ValidationError('시간에는 시간대 오프셋이 필요합니다.')
        ended_at = normalized(ended_at)
        status_field = 'status' if model is PlaySession else 'outcome'
        allowed = ('completed', 'abandoned') if model is PlaySession else ('success', 'failure', 'abandoned')
        if outcome not in allowed or timezone.is_naive(ended_at) or ended_at < record.started_at:
            raise ValidationError('종료 상태 또는 시각이 잘못되었습니다.')
        if record.ended_at:
            if record.ended_at == ended_at and getattr(record, status_field) == outcome:
                return record
            raise ValidationError('종료된 기록을 덮어쓸 수 없습니다.')
        if model is PlaySession:
            if collection(TaskRun).find_one({'session_id': str(record.pk), 'ended_at': None}):
                raise ValidationError('진행 중인 문제를 먼저 종료하세요.')
            latest = collection(BehaviorEvent).find_one({'session_id': str(record.pk)}, sort=[('occurred_at', -1)])
            if latest and latest['occurred_at'] > ended_at:
                raise ValidationError('마지막 이벤트보다 일찍 세션을 종료할 수 없습니다.')
            record.duration_ms = round((ended_at-record.started_at).total_seconds()*1000)
        else:
            run = get_record(TaskRun, record.run_id)
            if run.ended_at:
                raise ValidationError('문제가 이미 종료되었습니다.')
            latest = collection(BehaviorEvent).find_one({'attempt_id': str(record.pk)}, sort=[('occurred_at', -1)])
            if latest and latest['occurred_at'] > ended_at:
                raise ValidationError('마지막 이벤트보다 일찍 시도를 종료할 수 없습니다.')
        record.ended_at = ended_at
        setattr(record, status_field, outcome)
        # Only update record fields; preserve a session's held lock until finally releases it.
        changes = document(record)
        changes.pop('_id')
        collection(model).update_one({'_id': str(record.pk)}, {'$set': changes})
        return record


@contextmanager
def session_lock(session_id):
    # Standalone MongoDB supports atomic single-document updates, not multi-document transactions.
    # Serialize all application writes/finalization for one game session.
    owner = str(uuid.uuid4())
    now = timezone.now()
    locked = collection(PlaySession).update_one(
        {'_id': str(session_id), '$or': [{'write_lock': {'$exists': False}}, {'write_lock.expires': {'$lt': now}}]},
        {'$set': {'write_lock': {'owner': owner, 'expires': now + timedelta(minutes=2)}}})
    if not locked.modified_count:
        raise ValidationError('Session is busy or missing; retry later.')
    try:
        yield
    finally:
        collection(PlaySession).update_one({'_id': str(session_id), 'write_lock.owner': owner}, {'$unset': {'write_lock': ''}})


def validate_fields(instance):
    # FK existence is validated explicitly against MongoDB/MySQL below, never via log ORM queries.
    instance.full_clean(exclude=[field.name for field in instance._meta.fields if field.is_relation],
                        validate_unique=False, validate_constraints=False)
    for name in ('started_at', 'ended_at', 'occurred_at'):
        value = getattr(instance, name, None)
        if value is not None and timezone.is_naive(value):
            raise ValidationError('Timestamps must include a timezone offset.')
    if getattr(instance, 'ended_at', None) and instance.ended_at < instance.started_at:
        raise ValidationError('End time must not precede start time.')


def create_record(instance):
    if isinstance(instance, BehaviorEvent):
        raise ValidationError('Use record_event to write behavior events.')
    if isinstance(instance, PlaySession):
        instance.player = Player.objects.get(pk=instance.player_id)
        validate_fields(instance)
        return insert_record(instance)
    if isinstance(instance, LearningTask):
        validate_fields(instance)
        return insert_record(instance)
    if isinstance(instance, TaskRun):
        instance.session = get_record(PlaySession, instance.session_id)
        instance.task = get_record(LearningTask, instance.task_id)
        session_id = instance.session_id
    elif isinstance(instance, SolveAttempt):
        instance.run = get_record(TaskRun, instance.run_id)
        session_id = instance.run.session_id
    else:
        raise ValidationError('Unsupported record type.')
    with session_lock(session_id):
        if isinstance(instance, SolveAttempt):
            instance.run = get_record(TaskRun, instance.run_id)
            if instance.run.ended_at:
                raise ValidationError('Cannot add an attempt to a finalized run.')
            if instance.number < 1 or instance.started_at < instance.run.started_at:
                raise ValidationError('Invalid attempt number or start time.')
        else:
            if instance.session.ended_at or instance.started_at < instance.session.started_at:
                raise ValidationError('Session is closed or run start time is invalid.')
        validate_fields(instance)
        return insert_record(instance)


def record_event(**fields):
    event = BehaviorEvent(**fields)
    event.session = get_record(PlaySession, event.session_id)
    for value in (event.state_before, event.state_after, event.payload):
        validate_metadata(value)
    # received_at is generated once, and is not part of retry identity.
    event.received_at = timezone.now()
    with session_lock(event.session_id):
        existing = collection(BehaviorEvent).find_one({'_id': str(event.pk)})
        if existing:
            event.received_at = existing['received_at']
            return insert_record(event)
        if event.run_id:
            event.run = get_record(TaskRun, event.run_id)
            if event.run.ended_at:
                raise ValidationError('Cannot add a new event to a finalized run.')
        if event.attempt_id:
            event.attempt = get_record(SolveAttempt, event.attempt_id)
        validate_fields(event)
        if event.sequence < 1:
            raise ValidationError('Event sequence must be at least one.')
        if event.occurred_at < event.session.started_at or (event.session.ended_at and event.occurred_at > event.session.ended_at):
            raise ValidationError('Event time is outside the session.')
        if event.run_id and event.occurred_at < event.run.started_at:
            raise ValidationError('Event time precedes the run.')
        return insert_record(event)


def finalize_run(run, status, ended_at):
    with session_lock(run.session_id):
        run = get_record(TaskRun, run.pk)
        if timezone.is_naive(ended_at):
            raise ValidationError('시간에는 시간대 오프셋이 필요합니다.')
        ended_at = normalized(ended_at)
        if status not in ('completed', 'abandoned') or timezone.is_naive(ended_at) or ended_at < run.started_at:
            raise ValidationError('Invalid final status or end time.')
        if run.ended_at:
            if run.ended_at == ended_at and run.status == status:
                return run
            raise ValidationError('Cannot overwrite a finalized run.')
        if status == 'completed' and not collection(SolveAttempt).find_one({'run_id': str(run.pk), 'outcome': 'success'}):
            raise ValidationError('A completed run requires a successful attempt.')
        paused_at = None
        paused_ms = 0
        for event in collection(BehaviorEvent).find({'run_id': str(run.pk)}).sort([('occurred_at', 1), ('sequence', 1)]):
            stamp = event['occurred_at']
            if not run.started_at <= stamp <= ended_at:
                raise ValidationError('An event is outside the run time window.')
            if event['event_type'] == 'paused':
                if paused_at is not None:
                    raise ValidationError('Nested pause events are invalid.')
                paused_at = stamp
            elif event['event_type'] == 'resumed':
                if paused_at is None:
                    raise ValidationError('Cannot resume without pausing.')
                paused_ms += round((stamp - paused_at).total_seconds() * 1000)
                paused_at = None
        if paused_at is not None:
            paused_ms += round((ended_at - paused_at).total_seconds() * 1000)
        elapsed_ms = round((ended_at - run.started_at).total_seconds() * 1000)
        run.status, run.ended_at = status, ended_at
        run.paused_ms, run.active_ms = paused_ms, elapsed_ms - paused_ms
        run.session = get_record(PlaySession, run.session_id)
        run.task = get_record(LearningTask, run.task_id)
        validate_fields(run)
        collection(TaskRun).replace_one({'_id': str(run.pk)}, document(run))
        return run
