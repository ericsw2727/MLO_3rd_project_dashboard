from collections import defaultdict
from datetime import datetime, time, timedelta
from django.utils import timezone
from .mongo import Records


def selected_runs(form, players):
    return getattr(form, 'mongo_runs', Records())


def learning_report(form, players):
    """Problem metrics use runs started in the window, followed through current outcome.

    Legacy events without run links are never guessed into problem/attempt metrics.
    """
    if not form.is_valid():
        return {'runs': 0, 'tasks': [], 'failures': [], 'hint_evaluable': 0, 'hint_next_success': 0}
    runs = selected_runs(form, players)
    runs = list(runs.select_related('task').prefetch_related('attempts', 'events'))
    groups = {}
    evaluable, helped, completed, abandoned, retry_runs = 0, 0, 0, 0, 0
    active_times = []
    for run in runs:
        task = run.task
        row = groups.setdefault(task.pk, {'task_id': task.task_id, 'version': task.content_version, 'title': task.title,
            'topic': task.get_topic_display(), 'runs': 0, 'completed': 0, 'abandoned': 0, 'attempts': 0,
            'retry_runs': 0, 'hint_runs': 0, 'active_times': []})
        attempts = sorted(run.attempts.all(), key=lambda a: (a.started_at, a.number))
        row['runs'] += 1
        row['attempts'] += len(attempts)
        if len(attempts) > 1:
            row['retry_runs'] += 1
            retry_runs += 1
        if run.status == 'completed':
            completed += 1
            row['completed'] += 1
            if run.active_ms is not None:
                active_times.append(run.active_ms)
                row['active_times'].append(run.active_ms)
        if run.status == 'abandoned':
            abandoned += 1
            row['abandoned'] += 1
        hints = sorted((e for e in run.events.all() if e.event_type == 'hint'), key=lambda e: (e.occurred_at, e.sequence))
        if hints:
            row['hint_runs'] += 1
            # One observation per run: first hint -> next attempt that started after it.
            following = next((a for a in attempts if a.started_at > hints[0].occurred_at), None)
            if following and following.outcome in ('success', 'failure'):
                evaluable += 1
                helped += int(following.outcome == 'success')
    for row in groups.values():
        row['completion_rate'] = round(100 * row['completed'] / row['runs'], 1)
        row['abandon_rate'] = round(100 * row['abandoned'] / row['runs'], 1)
        times = row.pop('active_times')
        row['avg_active_seconds'] = round(sum(times) / len(times) / 1000, 1) if times else None
    # A run cohort is followed to completion; these failures may occur after the selected end date.
    failure_rows = [(event.operation, event.failure_reason) for run in runs for event in run.events.all() if event.event_type == 'operation_failed']
    failures = defaultdict(int)
    for operation, reason in failure_rows:
        failures[(operation or 'unknown', reason or 'unknown')] += 1
    return {'runs': len(runs), 'completed': completed, 'abandoned': abandoned, 'retry_runs': retry_runs,
            'completion_rate': round(100 * completed / len(runs), 1) if runs else None,
            'avg_active_seconds': round(sum(active_times)/len(active_times)/1000, 1) if active_times else None,
            'hint_evaluable': evaluable, 'hint_next_success': helped,
            'hint_next_rate': round(100 * helped/evaluable, 1) if evaluable else None,
            'tasks': sorted(groups.values(), key=lambda r: (-r['abandon_rate'], r['completion_rate'], r['task_id'], r['version'])),
            'failures': [{'operation': k[0], 'reason': k[1], 'count': v} for k, v in sorted(failures.items(), key=lambda item: (-item[1], item[0]))]}
