"""Read the pipeline's learning events (MongoDB pipeline_learning_events) for staff screens.

The game currently sends its install ID as player_id, so events are tied to members
through the install IDs recorded in game_login_history. Member IDs are matched too,
for when the game switches to sending the logged-in member ID.
"""
from .catalog import CATALOG
from .models import GameAccount, GameLoginRecord
from .mongo import Records, database

EVENT_LABELS = {
    'problem_started': '문제 시작', 'problem_completed': '문제 완료', 'attempt_started': '시도 시작',
    'attempt_succeeded': '시도 성공', 'attempt_failed': '시도 실패', 'operation_succeeded': '조작 성공',
    'operation_failed': '조작 실패', 'hint_used': '힌트 사용',
}


def member_keys(player, install_ids=None):
    """Every player_id value an event for this member may carry."""
    if install_ids is None:
        install_ids = GameLoginRecord.objects.filter(player=player).values_list('install_id', flat=True).distinct()
    return sorted({str(player.pk), player.pk.hex, *(i for i in install_ids if i)})


def identity_map():
    """player_id value in events -> {'name', 'pk'} for known members."""
    names = {a.player_id: a.username for a in GameAccount.objects.only('username', 'player_id')}
    found = {}
    for pk, name in names.items():
        found[str(pk)] = found[pk.hex] = {'name': name, 'pk': pk}
    rows = GameLoginRecord.objects.exclude(install_id='').exclude(player=None).order_by('occurred_at')
    for install_id, pk in rows.values_list('install_id', 'player_id'):
        if pk in names:  # the latest login on a device wins
            found[install_id] = {'name': names[pk], 'pk': pk}
    return found


class EventPage:
    """Paginator-friendly view over a MongoDB query: count() and slicing via skip/limit."""

    def __init__(self, query, newest_first=True):
        self.collection = database().pipeline_learning_events
        self.query = query
        self.direction = -1 if newest_first else 1
        self._count = None

    def count(self):
        if self._count is None:
            self._count = self.collection.count_documents(self.query)
        return self._count

    def __len__(self):
        return self.count()

    def __getitem__(self, item):
        start, stop = (item.start or 0), item.stop
        cursor = self.collection.find(self.query, sort=[('occurred_at', self.direction), ('sequence', self.direction)])
        return list(cursor.skip(start).limit(max(stop - start, 0)))


def describe(doc, identities):
    """Flatten one event document for templates."""
    details = doc.get('details') or {}
    code = doc.get('minigame_id') or ''
    raw_player = doc.get('player_id') or ''
    who = identities.get(raw_player)
    return {
        'at': doc.get('occurred_at'), 'code': code or '—', 'title': CATALOG.get(code, {}).get('title', ''),
        'kind': doc.get('event_type', ''), 'label': EVENT_LABELS.get(doc.get('event_type'), doc.get('event_type', '')),
        'operation': details.get('operation', ''), 'reason': details.get('failure_reason', ''),
        'build': doc.get('build_version', ''), 'content': doc.get('content_version', ''),
        'sequence': doc.get('sequence'), 'session': (doc.get('session_id') or '')[:8],
        'member': who, 'raw_player': raw_player,
    }


# Pipeline event type -> analytics (BehaviorEvent) event type.
ANALYTICS_TYPES = {'problem_started': 'task_started', 'problem_completed': 'task_completed', 'hint_used': 'hint'}


def _uuid(value, namespace):
    from uuid import NAMESPACE_URL, UUID, uuid5
    try:
        return UUID(str(value))
    except (TypeError, ValueError):
        return uuid5(NAMESPACE_URL, f'nodeverse:{namespace}:{value}')


def analytics_snapshot(members, start, end, filters):
    """Build sessions, runs, attempts and events (unsaved model objects) from pipeline_learning_events.

    Only events that resolve to one of `members` (by member ID or a logged-in install ID) are used,
    so the overview, game analysis and player pages count real members' play. Window events are those in
    [start, end); runs that started in the window are followed through all of their events, like load_snapshot.
    Returns dicts keyed by str(id): sessions, runs, events (window events), plus the cohort run keys.
    """
    from .catalog import game_for, selected_codes
    from .models import BehaviorEvent, LearningTask, PlaySession, SolveAttempt, TaskRun
    if filters.get('topic'):  # legacy stack/queue/tree topics do not exist in pipeline events
        return {}, {}, [], []
    member_by_pk = {str(m.pk): m for m in members}
    owner = {}
    for key, info in identity_map().items():
        member = member_by_pk.get(str(info['pk']))
        if member:
            owner[key] = member
    if not owner:
        return {}, {}, [], []
    base = {'player_id': {'$in': sorted(owner)}}
    if filters.get('category') or filters.get('game_id'):
        base['minigame_id'] = {'$in': selected_codes(filters)}
    if filters.get('task_id'):
        base['minigame_id'] = filters['task_id'].upper()
    if filters.get('content_version'):
        base['content_version'] = filters['content_version']
    col = database().pipeline_learning_events
    window = list(col.find({**base, 'occurred_at': {'$gte': start, '$lt': end}}))
    run_ids = {d.get('run_id') for d in window} - {None}
    docs = {d['_id']: d for d in window}
    docs.update({d['_id']: d for d in col.find({**base, 'run_id': {'$in': sorted(run_ids)}})})
    ordered = sorted(docs.values(), key=lambda d: (d['occurred_at'], d.get('sequence') or 0))

    sessions, tasks, runs, attempts, events = {}, {}, {}, {}, {}
    for d in ordered:
        member = owner[d['player_id']]
        at = d['occurred_at']
        code = (d.get('minigame_id') or 'UNKNOWN').upper()
        version = d.get('content_version') or 'base'
        game = game_for(code)
        sid = _uuid(d.get('session_id') or f"{d['player_id']}:{d.get('run_id')}", 'session')
        session = sessions.get(str(sid))
        if session is None:
            session = sessions[str(sid)] = PlaySession(id=sid, player=member, topic=game['area'] if game else 'unmapped',
                                                       game_version=d.get('build_version') or '', started_at=at,
                                                       status='in_progress')
        session.ended_at = at
        tid = _uuid(f'{code}:{version}', 'task')
        task = tasks.setdefault(str(tid), LearningTask(id=tid, task_id=code, content_version=version,
                                                       title=game['title'] if game else code, topic=session.topic))
        run = None
        if d.get('run_id'):
            rid = _uuid(d['run_id'], 'run')
            run = runs.get(str(rid))
            if run is None:
                run = runs[str(rid)] = TaskRun(id=rid, session=session, task=task, started_at=at, status='in_progress')
                run._prefetched_objects_cache = {'attempts': Records(), 'events': Records()}
        attempt = None
        if d.get('attempt_id') and run is not None:
            aid = _uuid(d['attempt_id'], 'attempt')
            attempt = attempts.get(str(aid))
            if attempt is None:
                attempt = attempts[str(aid)] = SolveAttempt(id=aid, run=run, number=len(run._prefetched_objects_cache['attempts']) + 1,
                                                            started_at=at, outcome='in_progress')
                run._prefetched_objects_cache['attempts'].append(attempt)
        kind = d.get('event_type', '')
        if attempt is not None and kind in ('attempt_succeeded', 'attempt_failed'):
            attempt.outcome, attempt.ended_at = ('success' if kind == 'attempt_succeeded' else 'failure'), at
        if run is not None and kind == 'problem_completed':
            run.status, run.ended_at = 'completed', at
            run.active_ms = int((at - run.started_at).total_seconds() * 1000)
        if kind == 'problem_completed':
            session.status = 'completed'
        details = d.get('details') or {}
        event = BehaviorEvent(id=_uuid(d['_id'], 'event'), session=session, sequence=d.get('sequence') or 0,
                              event_type=ANALYTICS_TYPES.get(kind, kind), run=run, attempt=attempt,
                              operation=str(details.get('operation', ''))[:40], failure_reason=str(details.get('failure_reason', ''))[:80],
                              hint_id=str(details.get('hint_id', '')), hint_step=details.get('hint_step') or (1 if kind == 'hint_used' else None),
                              occurred_at=at, payload=details)
        if run is not None:
            run._prefetched_objects_cache['events'].append(event)
        events[d['_id']] = event
    for session in sessions.values():
        session.duration_ms = int((session.ended_at - session.started_at).total_seconds() * 1000)
    window_events = [events[d['_id']] for d in window]
    cohort = [r for r in runs.values() if start <= r.started_at < end]
    in_window = {str(k): s for k, s in sessions.items() if start <= s.started_at < end}
    return in_window, runs, window_events, cohort
