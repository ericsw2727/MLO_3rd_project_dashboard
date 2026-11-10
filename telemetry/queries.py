from collections import Counter
from datetime import datetime, time, timedelta
from django.db.models import Q
from django.utils import timezone
from .forms import AnalysisFilter
from .models import Player, PlaySession
from .mongo import Records, load_snapshot


def selection(params, player=None):
    filter_form = AnalysisFilter(params)
    players = Player.objects.all()
    if player:
        players = players.filter(pk=player.pk)
    if not filter_form.is_valid():
        filter_form.mongo_runs = Records()
        return filter_form, players.none(), Records(), Records()
    filters = filter_form.cleaned_data
    if filters['player_id']:
        players = players.filter(pk=filters['player_id'].pk)
    if filters['source'] != 'all':
        players = players.filter(source=filters['source'])
    if filters['q']:
        players = players.filter(Q(display_name__icontains=filters['q']) | Q(external_id__icontains=filters['q']))
    start = timezone.make_aware(datetime.combine(filters['start'], time.min))
    end = timezone.make_aware(datetime.combine(filters['end'] + timedelta(days=1), time.min))
    sessions, events, runs = load_snapshot(players, start, end, filters)
    filter_form.mongo_runs = runs
    return filter_form, players, sessions, events


def summary(players, sessions, events):
    kinds = Counter(event.event_type for event in events)
    successes = kinds['success'] + kinds['operation_succeeded']
    failures = kinds['failure'] + kinds['operation_failed']
    durations = [session.duration_ms for session in sessions if session.status == 'completed' and session.duration_ms is not None]
    return {'total': len(events), 'successes': successes, 'failures': failures,
            'attempts': kinds['attempt'] + kinds['attempt_started'], 'hints': kinds['hint'],
            'success_rate': round(100 * successes / (successes + failures), 1) if successes + failures else None,
            'players': players.count(), 'demo_players': players.filter(source='demo').count(),
            'sessions': len(sessions), 'completed': sum(session.status == 'completed' for session in sessions),
            'avg_seconds': round(sum(durations) / len(durations) / 1000) if durations else None,
            'active_players': len({event.session.player_id for event in events})}


def topic_breakdown(events):
    counts = {}
    for event in events:
        counts.setdefault(event.session.topic, Counter())[event.event_type] += 1
    rows = []
    for topic, kinds in sorted(counts.items()):
        successes = kinds['success'] + kinds['operation_succeeded']
        failures = kinds['failure'] + kinds['operation_failed']
        rows.append({'topic': dict(PlaySession.TOPICS).get(topic, topic), 'successes': successes,
                     'failures': failures, 'hints': kinds['hint'],
                     'rate': round(100 * successes / (successes + failures), 1) if successes + failures else None})
    return rows


def player_rows(players, sessions, events):
    session_counts = Counter(session.player_id for session in sessions)
    event_counts = {}
    for event in events:
        event_counts.setdefault(event.session.player_id, Counter())[event.event_type] += 1
    rows = []
    for player in players:
        kinds = event_counts.get(player.pk, Counter())
        successes = kinds['success'] + kinds['operation_succeeded']
        failures = kinds['failure'] + kinds['operation_failed']
        rows.append({'player': player, 'sessions': session_counts[player.pk], 'events': sum(kinds.values()),
                     'failures': failures, 'hints': kinds['hint'],
                     'rate': round(100 * successes / (successes + failures), 1) if successes + failures else None})
    return rows
