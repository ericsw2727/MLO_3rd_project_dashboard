from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from accounts.views import admin_page, api
from .models import Player, PlaySession
from .queries import selection, summary, topic_breakdown, player_rows
from .learning import learning_report
from .learning import selected_runs
from .visuals import visual_report
from .catalog import report as catalog_report, game_for
from datetime import timedelta
from django.utils import timezone
from django.http import HttpResponse
import csv


def context(request, player=None):
    filter_form, players, sessions, events = selection(request.GET, player)
    params = request.GET.copy()
    params.pop('page', None)
    return {'filter': filter_form, 'stats': summary(players, sessions, events), 'querystring': params.urlencode(),
            'today': timezone.localdate().isoformat(), 'week_start': (timezone.localdate()-timedelta(days=6)).isoformat(),
            'month_start': (timezone.localdate()-timedelta(days=27)).isoformat(),
            'topics': topic_breakdown(events), 'learning': learning_report(filter_form, players)}, players, sessions, events


@require_GET
@admin_page
def dashboard_page(request, scope=None):
    scope = scope or request.GET.get('scope', 'overview')
    if scope not in ('overview', 'game', 'player'):
        scope = 'overview'
    page_context, players, sessions, events = context(request)
    if scope == 'player':
        params = request.GET.copy()
        params.pop('scope', None)
        player_id = params.pop('player_id', [None])[-1]
        if player_id:
            from uuid import UUID
            try:
                target = '/staff/players/' + str(UUID(player_id)) + '/'
            except ValueError:
                target = '/staff/players/'
        else:
            target = '/staff/players/'
        return redirect(target + ('?' + params.urlencode() if params else ''))
    page_context.update({'scope': scope, 'scope_title': '게임 분석' if scope == 'game' else '전체 현황',
        'scope_description': '게임을 선택해 풀이 과정과 실패 원인을 확인하세요.' if scope == 'game' else '전체 학습 흐름과 확인이 필요한 기록을 요약합니다.'})
    catalog = catalog_report(selected_runs(page_context['filter'], players), events)
    for area in catalog['areas']:
        params = request.GET.copy()
        for field in ('page', 'game_id', 'task_id', 'content_version', 'topic'):
            params.pop(field, None)
        params.pop('scope', None)
        params['category'] = area['key']
        area['url'] = '/staff/games/?' + params.urlencode()
    for game in catalog['games']:
        params = request.GET.copy()
        for field in ('page', 'task_id', 'content_version', 'topic'):
            params.pop(field, None)
        params.pop('scope', None)
        params['category'] = game['area']
        params['game_id'] = game['code']
        game['url'] = '/staff/games/?' + params.urlencode()
        game['events_url'] = '/staff/events/?' + params.urlencode()
    cleaned = page_context['filter'].cleaned_data
    catalog['visible_games'] = [g for g in catalog['games']
        if (not cleaned.get('category') or g['area'] == cleaned['category'])
        and (not cleaned.get('game_id') or g['code'] == cleaned['game_id'])]
    page_context['catalog'] = catalog
    selected_game = game_for(cleaned.get('game_id', ''))
    page_context['selected_game'] = selected_game
    if selected_game:
        page_context['scope_title'] = selected_game['title']
        page_context['scope_description'] = selected_game['code'] + ' · ' + selected_game['concept']
    page_context['show_analysis'] = scope == 'overview' or bool(selected_game)
    page_context['compact_charts'] = scope == 'overview'
    page_context['recent_events'] = events.select_related('session__player', 'run__task', 'attempt').order_by('-occurred_at', '-sequence')[:8]
    if page_context['show_analysis']:
        page_context['visuals'] = visual_report(page_context['filter'], players, events)
    return render(request, 'telemetry/dashboard.html', page_context)


@require_GET
@admin_page
def players_page(request):
    page_context, players, sessions, events = context(request)
    sort_options = [('name', '이름 오름차순'), ('name_desc', '이름 내림차순'), ('recent', '최근 등록순')]
    selected_sort = request.GET.get('sort', 'name')
    ordering = {'name': ('display_name', 'id'), 'name_desc': ('-display_name', 'id'), 'recent': ('-created_at', 'id')}
    if selected_sort not in ordering:
        selected_sort = 'name'
    page = Paginator(players.order_by(*ordering[selected_sort]), 10).get_page(request.GET.get('page'))
    page_context.update({'page': page, 'rows': player_rows(page.object_list, sessions, events),
                         'sort_options': sort_options, 'selected_sort': selected_sort})
    return render(request, 'telemetry/players.html', page_context)


@require_GET
@admin_page
def player_page(request, player_id):
    player = get_object_or_404(Player, pk=player_id)
    page_context, players, sessions, events = context(request, player)
    page_context.update({'player': player, 'sessions': sessions.order_by('-started_at')[:20],
                'page': Paginator(events.select_related('session__player','run__task','attempt').order_by('-occurred_at', '-sequence'), 20).get_page(request.GET.get('page'))})
    page_context['visuals'] = visual_report(page_context['filter'], players, events)
    return render(request, 'telemetry/player.html', page_context)


@require_GET
@admin_page
def events_page(request):
    page_context, players, sessions, events = context(request)
    if page_context['filter'].is_valid() and page_context['filter'].cleaned_data['event_type']:
        events = events.filter(event_type=page_context['filter'].cleaned_data['event_type'])
    selected_sort = 'oldest' if request.GET.get('sort') == 'oldest' else 'recent'
    ordering = ('occurred_at', 'sequence', 'id') if selected_sort == 'oldest' else ('-occurred_at', '-sequence', '-id')
    page_context['page'] = Paginator(events.select_related('session__player','run__task','attempt').order_by(*ordering), 30).get_page(request.GET.get('page'))
    page_context.update({'sort_options': [('recent', '최신 발생순'), ('oldest', '오래된 발생순')], 'selected_sort': selected_sort})
    return render(request, 'telemetry/events.html', page_context)


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
    filter_form, players, sessions, events = selection(request.GET)
    if not filter_form.is_valid():
        return JsonResponse({'errors': filter_form.errors.get_json_data()}, status=400)
    return JsonResponse({'summary': summary(players, sessions, events), 'topics': topic_breakdown(events),
                         'learning': learning_report(filter_form, players)})


@api('GET', authenticated=True)
def visuals_api(request):
    filter_form, players, sessions, events = selection(request.GET)
    if not filter_form.is_valid():
        return JsonResponse({'errors': filter_form.errors.get_json_data()}, status=400)
    return JsonResponse(visual_report(filter_form, players, events))


@require_GET
@admin_page
def guide_page(request):
    return render(request, 'telemetry/guide.html')


@require_GET
@admin_page
def export_runs(request):
    filter_form, players, sessions, events = selection(request.GET)
    if not filter_form.is_valid():
        return JsonResponse({'errors': filter_form.errors.get_json_data()}, status=400)
    response=HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition']='attachment; filename="nodeverse-runs.csv"'
    response.write('\ufeff')
    writer=csv.writer(response)
    writer.writerow(['player_id','display_name','source','run_id','task_id','version','status','started_at','active_seconds','paused_seconds','game_id','game_title','category'])
    for run in selected_runs(filter_form,players).select_related('session__player','task').order_by('started_at','id').iterator():
        game = game_for(run.task.task_id)
        row=[run.session.player_id,run.session.player.display_name,run.session.player.source,run.pk,run.task.task_id,
                         run.task.content_version,run.status,run.started_at.isoformat(),
                         run.active_ms/1000 if run.active_ms is not None else '',run.paused_ms/1000,
                         game['code'] if game else '', game['title'] if game else '', game['area'] if game else 'unmapped']
        writer.writerow(["'"+value if isinstance(value,str) and value.startswith(('=', '+', '-', '@', '\t', '\r', '\n')) else value for value in row])
    return response


@api('GET', authenticated=True)
def players_api(request):
    filter_form, players, sessions, events = selection(request.GET)
    if not filter_form.is_valid():
        return JsonResponse({'errors': filter_form.errors.get_json_data()}, status=400)
    page = Paginator(players.order_by('display_name', 'id'), 10).get_page(request.GET.get('page'))
    return JsonResponse({'count': page.paginator.count, 'page': page.number, 'results': [
        {**player_data(row['player']), **{k: v for k, v in row.items() if k != 'player'}}
        for row in player_rows(page.object_list, sessions, events)]})


@api('GET', authenticated=True)
def player_api(request, player_id):
    player = Player.objects.filter(pk=player_id).first()
    if player is None:
        return JsonResponse({'error': 'not_found'}, status=404)
    filter_form, players, sessions, events = selection(request.GET, player)
    if not filter_form.is_valid():
        return JsonResponse({'errors': filter_form.errors.get_json_data()}, status=400)
    return JsonResponse({'player': player_data(player), 'summary': summary(players, sessions, events),
                         'topics': topic_breakdown(events), 'learning': learning_report(filter_form, players)})


@api('GET', authenticated=True)
def events_api(request):
    filter_form, players, sessions, events = selection(request.GET)
    if not filter_form.is_valid():
        return JsonResponse({'errors': filter_form.errors.get_json_data()}, status=400)
    if filter_form.cleaned_data['event_type']:
        events = events.filter(event_type=filter_form.cleaned_data['event_type'])
    page = Paginator(events.select_related('session__player','run__task','attempt').order_by('-occurred_at', '-sequence'), 30).get_page(request.GET.get('page'))
    return JsonResponse({'count': page.paginator.count, 'page': page.number, 'results': [event_data(event) for event in page]})
