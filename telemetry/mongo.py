"""Explicit MongoDB persistence; Django log models are validation/display objects only."""
from functools import lru_cache
from datetime import datetime, timezone as datetime_timezone
from uuid import UUID

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.http import JsonResponse, HttpResponse
from pymongo import MongoClient
from pymongo.errors import PyMongoError, DuplicateKeyError

from .models import Player, PlaySession, LearningTask, TaskRun, SolveAttempt, BehaviorEvent

LOG_MODELS = (PlaySession, LearningTask, TaskRun, SolveAttempt, BehaviorEvent)


@lru_cache(maxsize=4)
def _client(uri):
    return MongoClient(uri, tz_aware=True, serverSelectionTimeoutMS=5000, connectTimeoutMS=5000,
                       socketTimeoutMS=10000)


def database():
    if not settings.MONGODB_URI:
        raise ImproperlyConfigured('MONGODB_URI를 설정하세요.')
    return _client(settings.MONGODB_URI)[settings.MONGODB_DATABASE]


def collection(model):
    return database()[model._meta.db_table]


def initialize_indexes():
    db = database()
    db.game_sessions.create_index([('player_id', 1), ('started_at', 1)])
    db.game_sessions.create_index([('topic', 1), ('started_at', 1)])
    db.game_problems.create_index([('task_id', 1), ('content_version', 1)], unique=True)
    db.problem_runs.create_index([('session_id', 1), ('started_at', 1)])
    db.problem_runs.create_index([('task_id', 1), ('started_at', 1)])
    db.solution_attempts.create_index([('run_id', 1), ('number', 1)], unique=True)
    db.gameplay_events.create_index([('session_id', 1), ('sequence', 1)], unique=True)
    db.gameplay_events.create_index([('run_id', 1), ('occurred_at', 1)])
    db.gameplay_events.create_index([('occurred_at', 1), ('event_type', 1)])


def normalized(value):
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, datetime):
        # BSON stores milliseconds, always compare at that same precision.
        value = value.astimezone(datetime_timezone.utc)
        return value.replace(microsecond=value.microsecond // 1000 * 1000)
    if isinstance(value, dict):
        return {key: normalized(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [normalized(item) for item in value]
    return value


def document(instance):
    return {'_id' if field.primary_key else field.attname: normalized(getattr(instance, field.attname))
            for field in instance._meta.concrete_fields}


def from_document(model, data):
    fields = {}
    for field in model._meta.concrete_fields:
        value = data.get('_id' if field.primary_key else field.attname, field.get_default())
        if value is not None and (field.primary_key or field.is_relation):
            value = UUID(value)
        fields[field.attname] = value
    return model(**fields)


def get_record(model, record_id):
    result = collection(model).find_one({'_id': str(record_id)})
    if result is None:
        raise ValidationError(f'{model.__name__} 기록이 없습니다.')
    return from_document(model, result)


def insert_record(instance):
    """Immutable identity; exact retries are idempotent, conflicting retries fail."""
    data = document(instance)
    try:
        collection(type(instance)).insert_one(data)
        return instance, True
    except DuplicateKeyError:
        existing = collection(type(instance)).find_one({'_id': data['_id']})
        if existing == data:
            return from_document(type(instance), existing), False
        raise ValidationError('기록 ID 또는 순서가 기존 내용과 충돌합니다.') from None


class Records(list):
    """Small in-memory result view used after indexed MongoDB filtering."""
    def all(self):
        return self

    def count(self):
        return len(self)

    def filter(self, **conditions):
        def attribute(record, path):
            for name in path.split('__'):
                record = getattr(record, name)
                if record is None:
                    return None
            return record
        def matches(record):
            for path, expected in conditions.items():
                if path.endswith('__isnull'):
                    if (attribute(record, path[:-8]) is None) != expected:
                        return False
                elif attribute(record, path) != expected:
                    return False
            return True
        return Records(record for record in self if matches(record))

    def order_by(self, *fields):
        result = Records(self)
        for field in reversed(fields):
            result.sort(key=lambda record: getattr(record, field.lstrip('-')), reverse=field.startswith('-'))
        return result

    def select_related(self, *args):
        return self  # Relationships are attached in a single snapshot load below.

    prefetch_related = select_related

    def iterator(self):
        return iter(self)

    def values_list(self, field, flat=False):
        return Records(getattr(record, field) if flat else (getattr(record, field),) for record in self)


def load_snapshot(members, start, end, filters):
    """Two time scopes: event window and started-run cohort followed to current outcome."""
    member_map = {str(member.pk): member for member in members}
    db = database()
    sessions = {doc['_id']: from_document(PlaySession, doc) for doc in db.game_sessions.find({
        'player_id': {'$in': list(member_map)}, **({'topic': filters['topic']} if filters['topic'] else {})})}
    problem_query = {key: filters[key] for key in ('task_id', 'content_version') if filters[key]}
    catalog_filter = bool(filters.get('category') or filters.get('game_id'))
    if catalog_filter:
        from .catalog import selected_codes
        pattern = '^(' + '|'.join(selected_codes(filters)) + ')$'
        problem_query['$and'] = [{'task_id': {'$regex': pattern, '$options': 'i'}}]
    if filters['topic']:
        problem_query['topic'] = filters['topic']
    problems = {doc['_id']: from_document(LearningTask, doc) for doc in db.game_problems.find(problem_query)}
    run_query = {'session_id': {'$in': list(sessions)}, 'task_id': {'$in': list(problems)}}
    matching_session_ids = None
    if filters['task_id'] or filters['content_version'] or catalog_filter:
        matching_session_ids = set(db.problem_runs.distinct('session_id', run_query))
    cohort_docs = list(db.problem_runs.find({**run_query, 'started_at': {'$gte': start, '$lt': end}}))
    runs = {doc['_id']: from_document(TaskRun, doc) for doc in cohort_docs}
    event_query = {'session_id': {'$in': list(sessions)}, 'occurred_at': {'$gte': start, '$lt': end}}
    if filters['task_id'] or filters['content_version'] or catalog_filter:
        event_query['run_id'] = {'$in': db.problem_runs.distinct('_id', run_query)}
    window_events = list(db.gameplay_events.find(event_query))
    extra_run_ids = {doc.get('run_id') for doc in window_events} - {None} - set(runs)
    for doc in db.problem_runs.find({'_id': {'$in': list(extra_run_ids)}}):
        runs[doc['_id']] = from_document(TaskRun, doc)
    missing_problem_ids = {str(run.task_id) for run in runs.values()} - set(problems)
    for doc in db.game_problems.find({'_id': {'$in': list(missing_problem_ids)}}):
        problems[doc['_id']] = from_document(LearningTask, doc)
    attempts = {doc['_id']: from_document(SolveAttempt, doc) for doc in db.solution_attempts.find({'run_id': {'$in': list(runs)}})}
    event_docs = {doc['_id']: doc for doc in window_events}
    event_docs.update({doc['_id']: doc for doc in db.gameplay_events.find({'run_id': {'$in': list(runs)}})})
    events = {key: from_document(BehaviorEvent, doc) for key, doc in event_docs.items()}
    for key, session in sessions.items():
        session.player = member_map[str(session.player_id)]
    for run in runs.values():
        run.session = sessions[str(run.session_id)]
        run.task = problems[str(run.task_id)]
        run._prefetched_objects_cache = {'attempts': Records(), 'events': Records()}
    for attempt in attempts.values():
        attempt.run = runs[str(attempt.run_id)]
        attempt.run._prefetched_objects_cache['attempts'].append(attempt)
    for event in events.values():
        event.session = sessions[str(event.session_id)]
        if event.run_id:
            event.run = runs[str(event.run_id)]
            event.run._prefetched_objects_cache['events'].append(event)
        if event.attempt_id:
            event.attempt = attempts[str(event.attempt_id)]
    return (
        Records(session for key, session in sessions.items() if start <= session.started_at < end
                and (matching_session_ids is None or key in matching_session_ids)),
        Records(events[doc['_id']] for doc in window_events),
        Records(runs[doc['_id']] for doc in cohort_docs),
    )


class MongoAvailabilityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        if not isinstance(exception, (PyMongoError, ImproperlyConfigured)):
            return None
        if request.path.startswith('/api/'):
            return JsonResponse({'error': 'log_storage_unavailable'}, status=503)
        return HttpResponse('로그 저장소에 연결할 수 없습니다. 잠시 후 다시 시도해 주세요.', status=503)
