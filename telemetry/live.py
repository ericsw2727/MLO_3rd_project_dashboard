"""Real-time screens (S2, S3, S5-2) and the game member screen.

Django never reads Delta. It only reads the MongoDB rt_* collections the pipeline
writes from Gold. Member progress comes from the MySQL cloud save (game_accounts.save_data).
Pipeline is the only writer; every read here is side-effect free.
"""
from collections import Counter
from datetime import datetime, timedelta, timezone as dt_timezone

from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_GET

from accounts.views import admin_page, api
from .catalog import AREAS, CATALOG, classify
from .models import GameAccount, GameLoginRecord
from .mongo import database
from .releases import active_pack, active_release, build_key

STALE_SECONDS = 30


def _minutes(request, default):
    raw = request.GET.get('minutes', str(default))
    try:
        value = int(raw)
    except ValueError:
        return None
    return value if 1 <= value <= 180 else None


def _iso(value):
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=dt_timezone.utc)
        return value.astimezone(dt_timezone.utc).isoformat().replace('+00:00', 'Z')
    return value


def _clean(doc):
    return {key: _iso(value) for key, value in doc.items() if key != '_id'}


def _json(data, status=200):
    response = JsonResponse(data, status=status, json_dumps_params={'ensure_ascii': False})
    response['Cache-Control'] = 'no-store'
    return response


def _bad_minutes():
    return _json({'error': 'minutes_out_of_range', 'allowed': '1-180'}, status=400)


def _since(minutes):
    return timezone.now() - timedelta(minutes=minutes)


def summary_data():
    doc = database().rt_summary.find_one({'_id': 'global'}) or {}
    updated = doc.get('updated_at')
    if isinstance(updated, datetime) and updated.tzinfo is None:
        updated = updated.replace(tzinfo=dt_timezone.utc)
    age = (timezone.now() - updated).total_seconds() if isinstance(updated, datetime) else None
    return {'events_last_1m': doc.get('events_last_1m', 0), 'active_sessions_5m': doc.get('active_sessions_5m', 0),
            'updated_at': _iso(updated), 'age_seconds': round(age, 1) if age is not None else None,
            'stale': age is None or age > STALE_SECONDS}


@api('GET', authenticated=True)
def summary_api(request):
    return _json(summary_data())


@api('GET', authenticated=True)
def minigames_api(request):
    minutes = _minutes(request, 30)
    if minutes is None:
        return _bad_minutes()
    rows = []
    for doc in database().rt_minigame_1m.find({'window_start': {'$gte': _since(minutes)}}).sort('window_start', 1):
        rows.append({**_clean(doc), **classify(doc.get('minigame_id'), doc.get('category'))})
    areas = {key: {'area': key, 'label': label, 'attempts': 0, 'successes': 0, 'failures': 0} for key, label in AREAS}
    for row in rows:
        bucket = areas.get(row['area'])
        if bucket:
            for field in ('attempts', 'successes', 'failures'):
                bucket[field] += row.get(field) or 0
    games = [{'minigame_id': code, 'title': g['title'], 'area': g['area']} for code, g in CATALOG.items()]
    return _json({'minutes': minutes, 'rows': rows, 'areas': list(areas.values()), 'games': games,
                  'category_mismatches': sorted({r['minigame_id'] for r in rows if r['category_mismatch']})})


@api('GET', authenticated=True)
def alerts_api(request):
    minutes = _minutes(request, 60)
    if minutes is None:
        return _bad_minutes()
    cursor = database().rt_alerts.find({'window_start': {'$gte': _since(minutes)}, 'alert': True}).sort('window_start', -1)
    return _json({'minutes': minutes, 'alerts': [{**_clean(doc), **classify(doc.get('minigame_id'), doc.get('category'))}
                                                 for doc in cursor]})


def updates_data(minutes):
    db = database()
    windows = [_clean(doc) for doc in db.rt_updates.find({'window_start': {'$gte': _since(minutes)}}).sort('window_start', 1)]
    versions = [_clean(doc) for doc in db.rt_versions.find({})]
    release, pack = active_release(), active_pack()
    builds = [v for v in versions if v.get('kind') == 'build']
    contents = [v for v in versions if v.get('kind') == 'content']
    share = lambda items, version: next((v.get('share') for v in items if v.get('version') == version), 0) if version else None
    below_min = sum(v.get('installs') or 0 for v in builds
                    if release and build_key(v.get('version')) < build_key(release.min_build))
    # Last 15 minutes of pack downloads -> "consider disabling the pack" warning.
    recent_cut = _iso(_since(15))
    recent = [w for w in windows if str(w.get('window_start')) >= recent_cut]
    ok = sum(w.get('downloads_succeeded') or 0 for w in recent)
    bad = sum(w.get('downloads_failed') or 0 for w in recent)
    recent_rate = bad / (ok + bad) if ok + bad else None
    reasons = Counter()
    for w in windows:
        if w.get('top_failure_reason') and w.get('downloads_failed'):
            reasons[w['top_failure_reason']] += w['downloads_failed']
    prompted = sum(w.get('prompted') or 0 for w in windows)
    accepted = sum(w.get('accepted') or 0 for w in windows)
    return {
        'minutes': minutes, 'windows': windows, 'versions': versions,
        'active': {'build_version': release.build_version if release else None,
                   'min_build': release.min_build if release else None,
                   'content_version': pack.version if pack else 'base',
                   'build_share': share(builds, release.build_version if release else None),
                   'content_share': share(contents, pack.version if pack else 'base'),
                   'installs_below_min_build': below_min},
        'failure_reasons': [{'reason': k, 'count': n} for k, n in reasons.most_common()],
        'prompt_response': {'prompted': prompted, 'accepted': accepted,
                            'rate': round(accepted / prompted, 3) if prompted else None},
        'pack_warning': {'downloads_15m': ok + bad, 'failure_rate_15m': round(recent_rate, 3) if recent_rate is not None else None,
                         'review': bool(ok + bad >= 10 and recent_rate is not None and recent_rate >= 0.2)},
    }


@api('GET', authenticated=True)
def updates_api(request):
    minutes = _minutes(request, 60)
    if minutes is None:
        return _bad_minutes()
    return _json(updates_data(minutes))


@require_GET
@admin_page
def live_page(request):
    tab = 'updates' if request.GET.get('tab') == 'updates' else 'live'
    return render(request, 'telemetry/live.html', {'tab': tab, 'stale_seconds': STALE_SECONDS})



# ---------- game members: sign-ups, logins, cloud-save progress ----------
# Accounts and cloud saves live in MySQL game_accounts (written by the game auth API).

def _stars(value):
    if isinstance(value, bool):
        return 1 if value else 0
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, dict):
        return _stars(value.get('stars', value.get('best_stars', 1 if value else 0)))
    return 1 if value else 0


def save_progress(save_data):
    """Read the cloud save JSON. minigame_cleared keys are matched to catalog IDs when possible."""
    data = save_data if isinstance(save_data, dict) else {}
    cleared = data.get('minigame_cleared') if isinstance(data.get('minigame_cleared'), dict) else {}
    games, other = {}, {}
    for key, value in cleared.items():
        stars = _stars(value)
        code = str(key).upper()
        (games if code in CATALOG else other)[code if code in CATALOG else str(key)] = stars
    quizzes = data.get('cleared_quizzes') if isinstance(data.get('cleared_quizzes'), list) else []
    return {
        'games': games, 'other': other, 'cleared': len([s for s in list(games.values()) + list(other.values()) if s > 0]),
        'stars': sum(games.values()) + sum(other.values()), 'score': data.get('score'),
        'difficulty': data.get('difficulty'), 'zone': data.get('zone'), 'quizzes': len(quizzes),
        'has_saved_game': bool(data.get('has_saved_game')), 'last_saved': data.get('last_saved'),
    }


@require_GET
@admin_page
def members_page(request):
    query = request.GET.get('q', '').strip()
    accounts = GameAccount.objects.select_related('player').annotate(
        logins=Count('player__login_records', filter=Q(player__login_records__kind='login', player__login_records__success=True)),
        failures=Count('player__login_records', filter=Q(player__login_records__success=False)),
    ).order_by('-created_at')
    if query:
        accounts = accounts.filter(Q(username__icontains=query) | Q(player__display_name__icontains=query))
    page = Paginator(accounts, 25).get_page(request.GET.get('page'))
    rows = [{'account': account, 'player': account.player, 'progress': save_progress(account.save_data)} for account in page]
    today = timezone.localdate()
    day_start = timezone.make_aware(datetime.combine(today, datetime.min.time()))
    week = [today - timedelta(days=offset) for offset in range(6, -1, -1)]
    daily = Counter(timezone.localtime(t).date() for t in GameLoginRecord.objects.filter(
        kind='login', success=True, occurred_at__gte=day_start - timedelta(days=6)).values_list('occurred_at', flat=True))
    stats = {
        'members': GameAccount.objects.count(),
        'signups_today': GameAccount.objects.filter(created_at__gte=day_start).count(),
        'logins_today': daily.get(today, 0),
        'failed_today': GameLoginRecord.objects.filter(success=False, occurred_at__gte=day_start).count(),
    }
    peak = max([daily.get(d, 0) for d in week] + [1])
    return render(request, 'telemetry/members.html', {
        'page': page, 'rows': rows, 'query': query, 'stats': stats, 'total_games': len(CATALOG),
        'week': [{'date': d, 'count': daily.get(d, 0), 'pct': round(100 * daily.get(d, 0) / peak)} for d in week],
        'recent': GameLoginRecord.objects.select_related('player').order_by('-occurred_at')[:15],
    })


@require_GET
@admin_page
def member_detail_page(request, player_id):
    from django.shortcuts import get_object_or_404
    account = get_object_or_404(GameAccount.objects.select_related('player'), player_id=player_id)
    history = GameLoginRecord.objects.filter(player_id=player_id).order_by('-occurred_at')
    progress = save_progress(account.save_data)
    areas = []
    for key, label in AREAS:
        items = [{'code': code, **g, 'stars': progress['games'].get(code)} for code, g in CATALOG.items() if g['area'] == key]
        areas.append({'key': key, 'label': label, 'games': items, 'done': sum(1 for i in items if i['stars'])})
    return render(request, 'telemetry/member_detail.html', {
        'account': account, 'player': account.player, 'history': history[:50], 'areas': areas,
        'progress': progress, 'total_games': len(CATALOG),
    })
