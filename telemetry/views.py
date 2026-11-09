from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from accounts.views import admin_page, api
from .models import Player, PlaySession
from .queries import selection, summary, topic_breakdown, player_rows
from .learning import learning_report
from .learning import selected_runs
from .visuals import visual_report
from datetime import timedelta
from django.utils import timezone
from django.http import HttpResponse
import csv


def context(request, player=None):
    form, players, sessions, events = selection(request.GET, player)
    params = request.GET.copy()
    params.pop('page', None)
    return {'filter': form, 'stats': summary(players, sessions, events), 'querystring': params.urlencode(),
            'today': timezone.localdate().isoformat(), 'week_start': (timezone.localdate()-timedelta(days=6)).isoformat(),
            'month_start': (timezone.localdate()-timedelta(days=27)).isoformat(),
            'topics': topic_breakdown(events), 'learning': learning_report(form, players)}, players, sessions, events


@require_GET
@admin_page
def dashboard_page(request):
    scope = request.GET.get('scope', 'overview')
    if scope not in ('overview', 'game', 'player'):
        scope = 'overview'
    ctx, players, sessions, events = context(request)
    tabs = []
    for key, label in [('overview', '전체 종합'), ('game', '게임별'), ('player', '플레이어별')]:
        params = request.GET.copy()
        for field in ('page', 'player_id', 'q', 'topic', 'task_id', 'content_version'):
            params.pop(field, None)
        params['scope'] = key
        tabs.append({'key': key, 'label': label, 'url': '?' + params.urlencode()})
    ctx.update({'scope': scope, 'analysis_tabs': tabs,
                'scope_title': {'overview': '전체 종합 분석', 'game': '게임별 분석', 'player': '플레이어별 분석'}[scope],
                'scope_description': {'overview': '전체 플레이 현황과 게임 간 차이를 확인하세요.',
                    'game': '게임을 선택해 문제와 실패 원인을 살펴보세요.',
                    'player': '플레이어를 선택해 풀이 과정과 학습 흐름을 확인하세요.'}[scope]})
    if scope in ('overview', 'game'):
        rows = []
        comparison_params = request.GET.copy()
        comparison_params.pop('topic', None)
        _, comparison_players, comparison_sessions, comparison_events = selection(comparison_params)
        for key, label in PlaySession.TOPICS:
            params = request.GET.copy()
            params.update({'scope': 'game', 'topic': key})
            game_sessions = comparison_sessions.filter(topic=key)
            game_events = comparison_events.filter(session__topic=key)
            rows.append({'label': label, 'url': '?' + params.urlencode(),
                         'stats': summary(comparison_players, game_sessions, game_events)})
        ctx['game_rows'] = rows
    else:
        page = Paginator(players.order_by('display_name', 'id'), 10).get_page(request.GET.get('page'))
        rows = player_rows(page.object_list, sessions, events)
        for row in rows:
            params = request.GET.copy()
            params.pop('page', None)
            params['player_id'] = str(row['player'].pk)
            row['url'] = '?' + params.urlencode()
        ctx.update({'player_rows': rows, 'page': page})
        if ctx['filter'].is_valid():
            ctx['selected_player'] = ctx['filter'].cleaned_data['player_id']
    ctx['show_analysis'] = scope != 'player' or bool(ctx.get('selected_player'))
    ctx['recent_events'] = events.select_related('session__player', 'run__task', 'attempt').order_by('-occurred_at', '-sequence')[:8]
    if ctx['show_analysis']:
        ctx['visuals'] = visual_report(ctx['filter'], players, events)
    return render(request, 'telemetry/dashboard.html', ctx)


@require_GET
@admin_page
def players_page(request):
    ctx, players, sessions, events = context(request)
    page = Paginator(players.order_by('display_name', 'id'), 10).get_page(request.GET.get('page'))
    ctx.update({'page': page, 'rows': player_rows(page.object_list, sessions, events)})
    return render(request, 'telemetry/players.html', ctx)


@require_GET
@admin_page
def player_page(request, player_id):
    player = get_object_or_404(Player, pk=player_id)
    ctx, players, sessions, events = context(request, player)
    ctx.update({'player': player, 'sessions': sessions.order_by('-started_at')[:20],
                'page': Paginator(events.select_related('session__player','run__task','attempt').order_by('-occurred_at', '-sequence'), 20).get_page(request.GET.get('page'))})
    ctx['visuals'] = visual_report(ctx['filter'], players, events)
    return render(request, 'telemetry/player.html', ctx)


@require_GET
@admin_page
def events_page(request):
    ctx, players, sessions, events = context(request)
    if ctx['filter'].is_valid() and ctx['filter'].cleaned_data['event_type']:
        events = events.filter(event_type=ctx['filter'].cleaned_data['event_type'])
    ctx['page'] = Paginator(events.select_related('session__player','run__task','attempt').order_by('-occurred_at', '-sequence'), 30).get_page(request.GET.get('page'))
    return render(request, 'telemetry/events.html', ctx)


def player_data(player):
    return {'player_id': str(player.pk), 'external_id': player.external_id,
            'display_name': player.display_name, 'source': player.source}


def event_data(event):
    return {'event_id': str(event.pk), 'session_id': str(event.session_id),
            'player_id': str(event.session.player_id), 'sequence': event.sequence, 'event_type': event.event_type,
            'occurred_at': event.occurred_at.isoformat(), 'payload': event.payload, 'source': event.session.player.source,
            'run_id': str(event.run_id) if event.run_id else None, 'attempt_id': str(event.attempt_id) if event.attempt_id else None,
            'task_id': event.run.task.task_id if event.run_id else None,
            'content_version': event.run.task.content_version if event.run_id else None,
            'operation': event.operation, 'failure_reason': event.failure_reason,
            'state_before': event.state_before, 'state_after': event.state_after,
            'hint_id': event.hint_id, 'hint_step': event.hint_step}


@api('GET', authenticated=True)
def summary_api(request):
    form, players, sessions, events = selection(request.GET)
    if not form.is_valid():
        return JsonResponse({'errors': form.errors.get_json_data()}, status=400)
    return JsonResponse({'summary': summary(players, sessions, events), 'topics': topic_breakdown(events),
                         'learning': learning_report(form, players)})


@api('GET', authenticated=True)
def visuals_api(request):
    form, players, sessions, events = selection(request.GET)
    if not form.is_valid():
        return JsonResponse({'errors': form.errors.get_json_data()}, status=400)
    return JsonResponse(visual_report(form, players, events))


@require_GET
@admin_page
def guide_page(request):
    return render(request, 'telemetry/guide.html')


@require_GET
@admin_page
def export_runs(request):
    form, players, sessions, events = selection(request.GET)
    if not form.is_valid():
        return JsonResponse({'errors': form.errors.get_json_data()}, status=400)
    response=HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition']='attachment; filename="nodeverse-runs.csv"'
    response.write('\ufeff')
    writer=csv.writer(response)
    writer.writerow(['player_id','display_name','source','run_id','task_id','version','status','started_at','active_seconds','paused_seconds'])
    for run in selected_runs(form,players).select_related('session__player','task').order_by('started_at','id').iterator():
        row=[run.session.player_id,run.session.player.display_name,run.session.player.source,run.pk,run.task.task_id,
                         run.task.content_version,run.status,run.started_at.isoformat(),
                         run.active_ms/1000 if run.active_ms is not None else '',run.paused_ms/1000]
        writer.writerow(["'"+value if isinstance(value,str) and value.startswith(('=', '+', '-', '@', '\t', '\r', '\n')) else value for value in row])
    return response


@api('GET', authenticated=True)
def players_api(request):
    form, players, sessions, events = selection(request.GET)
    if not form.is_valid():
        return JsonResponse({'errors': form.errors.get_json_data()}, status=400)
    page = Paginator(players.order_by('display_name', 'id'), 10).get_page(request.GET.get('page'))
    return JsonResponse({'count': page.paginator.count, 'page': page.number, 'results': [
        {**player_data(row['player']), **{k: v for k, v in row.items() if k != 'player'}}
        for row in player_rows(page.object_list, sessions, events)]})


@api('GET', authenticated=True)
def player_api(request, player_id):
    player = Player.objects.filter(pk=player_id).first()
    if player is None:
        return JsonResponse({'error': 'not_found'}, status=404)
    form, players, sessions, events = selection(request.GET, player)
    if not form.is_valid():
        return JsonResponse({'errors': form.errors.get_json_data()}, status=400)
    return JsonResponse({'player': player_data(player), 'summary': summary(players, sessions, events),
                         'topics': topic_breakdown(events), 'learning': learning_report(form, players)})


@api('GET', authenticated=True)
def events_api(request):
    form, players, sessions, events = selection(request.GET)
    if not form.is_valid():
        return JsonResponse({'errors': form.errors.get_json_data()}, status=400)
    if form.cleaned_data['event_type']:
        events = events.filter(event_type=form.cleaned_data['event_type'])
    page = Paginator(events.select_related('session__player','run__task','attempt').order_by('-occurred_at', '-sequence'), 30).get_page(request.GET.get('page'))
    return JsonResponse({'count': page.paginator.count, 'page': page.number, 'results': [event_data(event) for event in page]})
