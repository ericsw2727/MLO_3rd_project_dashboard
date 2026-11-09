from datetime import datetime, time, timedelta
from django.db.models import Count, Avg, Q
from django.utils import timezone
from .forms import AnalysisFilter
from .models import Player, PlaySession, BehaviorEvent


def selection(params, player=None):
    form = AnalysisFilter(params)
    players, sessions, events = Player.objects.all(), PlaySession.objects.all(), BehaviorEvent.objects.all()
    if player:
        players = players.filter(pk=player.pk)
    if not form.is_valid():
        return form, players.none(), sessions.none(), events.none()
    data = form.cleaned_data
    if data['player_id']:
        players = players.filter(pk=data['player_id'].pk)
    if data['source'] != 'all':
        players = players.filter(source=data['source'])
    if data['q']:
        players = players.filter(Q(display_name__icontains=data['q']) | Q(external_id__icontains=data['q']))
    sessions = sessions.filter(player__in=players)
    if data['topic']:
        sessions = sessions.filter(topic=data['topic'])
    start = timezone.make_aware(datetime.combine(data['start'], time.min))
    end = timezone.make_aware(datetime.combine(data['end'] + timedelta(days=1), time.min))
    # Event windows use event time; session windows use session start time.
    events = events.filter(session__in=sessions, occurred_at__gte=start, occurred_at__lt=end)
    run_conditions = {}
    if data['task_id']:
        events = events.filter(run__task__task_id=data['task_id'])
        run_conditions['task_runs__task__task_id'] = data['task_id']
    if data['content_version']:
        events = events.filter(run__task__content_version=data['content_version'])
        run_conditions['task_runs__task__content_version'] = data['content_version']
    if run_conditions:
        sessions = sessions.filter(**run_conditions).distinct()
    sessions = sessions.filter(started_at__gte=start, started_at__lt=end)
    # event_type only filters the event browser, never changes headline metrics.
    return form, players, sessions, events


def summary(players, sessions, events):
    counts = events.aggregate(total=Count('id'), successes=Count('id', filter=Q(event_type__in=['success', 'operation_succeeded'])),
                             failures=Count('id', filter=Q(event_type__in=['failure', 'operation_failed'])),
                             attempts=Count('id', filter=Q(event_type__in=['attempt', 'attempt_started'])),
                             hints=Count('id', filter=Q(event_type='hint')))
    outcomes = counts['successes'] + counts['failures']
    counts['success_rate'] = round(counts['successes'] * 100 / outcomes, 1) if outcomes else None
    counts['players'] = players.count()
    counts['demo_players'] = players.filter(source='demo').count()
    counts['sessions'] = sessions.count()
    counts['completed'] = sessions.filter(status='completed').count()
    avg = sessions.filter(status='completed').aggregate(value=Avg('duration_ms'))['value']
    counts['avg_seconds'] = round(avg / 1000) if avg is not None else None
    counts['active_players'] = events.values('session__player').distinct().count()
    return counts


def topic_breakdown(events):
    rows = events.values('session__topic').annotate(
        successes=Count('id', filter=Q(event_type__in=['success', 'operation_succeeded'])),
        failures=Count('id', filter=Q(event_type__in=['failure', 'operation_failed'])),
        hints=Count('id', filter=Q(event_type='hint'))).order_by('session__topic')
    result = []
    for row in rows:
        total = row['successes'] + row['failures']
        result.append({'topic': dict(PlaySession.TOPICS).get(row['session__topic'], row['session__topic']),
                       'successes': row['successes'], 'failures': row['failures'], 'hints': row['hints'],
                       'rate': round(row['successes'] * 100 / total, 1) if total else None})
    return result


def player_rows(players, sessions, events):
    # Aggregate each relation separately to avoid multiplying sessions by their events.
    per_session = {row['player_id']: row for row in sessions.values('player_id').annotate(count=Count('id'))}
    per_event = {row['session__player_id']: row for row in events.values('session__player_id').annotate(
        total=Count('id'), successes=Count('id', filter=Q(event_type__in=['success', 'operation_succeeded'])),
        failures=Count('id', filter=Q(event_type__in=['failure', 'operation_failed'])), hints=Count('id', filter=Q(event_type='hint')))}
    rows = []
    for player in players:
        row = per_event.get(player.pk, {})
        outcomes = row.get('successes', 0) + row.get('failures', 0)
        rows.append({'player': player, 'sessions': per_session.get(player.pk, {}).get('count', 0),
                     'events': row.get('total', 0), 'failures': row.get('failures', 0), 'hints': row.get('hints', 0),
                     'rate': round(row.get('successes', 0) * 100 / outcomes, 1) if outcomes else None})
    return rows
