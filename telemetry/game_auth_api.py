"""Game client player authentication & cloud save API backed by MySQL (game_accounts + game_members).

Response JSON shapes are what the Godot client expects; keep them unchanged.
Server-side additions: every register/login/find-id/reset attempt is written to
game_login_history for the staff dashboard, and simple cache-based rate limits apply.
"""
import json
import re
import uuid

from django.contrib.auth.hashers import make_password, check_password
from django.core.cache import cache
from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt

from .models import Player, GameAccount, GameLoginRecord

IP_LIMIT = (30, 60)          # auth requests per IP per minute
FAILURE_LIMIT = (10, 600)    # failed logins/resets per username per 10 minutes
_VERSION_RE = re.compile(r'^[A-Za-z0-9._-]{1,40}$')
_INSTALL_RE = re.compile(r'^[A-Za-z0-9-]{1,64}$')
_DUMMY_HASH = make_password('nodeverse-timing-equalizer')


def _default_save_data(difficulty='NOVICE'):
    return {
        'difficulty': difficulty,
        'score': 0,
        'cleared_quizzes': [],
        'minigame_cleared': {},
        'player_pos': [0.0, 1.08, 12.15],
        'zone': 'MAIN',
        'has_saved_game': False,
    }


def _parse_json_body(request):
    if request.method != 'POST':
        return None, JsonResponse({'success': False, 'message': 'POST 요청만 허용됩니다.'}, status=405)
    try:
        if len(request.body) > 65536:
            return None, JsonResponse({'success': False, 'message': '요청 크기가 너무 큽니다.'}, status=413)
        data = json.loads(request.body.decode('utf-8'))
        if not isinstance(data, dict):
            raise ValueError
        return data, None
    except (ValueError, UnicodeDecodeError):
        return None, JsonResponse({'success': False, 'message': '올바른 JSON 형식이 아닙니다.'}, status=400)


def _bump(key, limit):
    _, window = limit
    cache.add(key, 0, window)
    try:
        return cache.incr(key)
    except ValueError:
        cache.set(key, 1, window)
        return 1


def _too_many(request):
    if _bump(f'game-auth-ip:{request.META.get("REMOTE_ADDR")}', IP_LIMIT) > IP_LIMIT[0]:
        return JsonResponse({'success': False, 'message': '요청이 너무 많습니다. 잠시 후 다시 시도해주세요.'}, status=429)
    return None


def _fail_key(username):
    return f'game-auth-fail:{username.lower()}'


def _record(request, data, kind, success, reason='', account=None, username=None):
    """Write one row to game_login_history. Never breaks the game request."""
    install = str(data.get('install_id', '') or '')
    build = str(data.get('build_version', '') or '')
    content = str(data.get('content_version', '') or '')
    login_id = username if username is not None else str(data.get('username', ''))
    try:
        GameLoginRecord.objects.create(
            player=account.player if account else None,
            login_id=login_id.strip()[:60],
            kind=kind, success=success, failure_reason=reason[:30],
            install_id=install if _INSTALL_RE.match(install) else '',
            build_version=build if _VERSION_RE.match(build) else '',
            content_version=content if _VERSION_RE.match(content) else '',
            ip_address=request.META.get('REMOTE_ADDR') or None,
        )
    except Exception:
        pass


@csrf_exempt
@never_cache
def game_auth_register(request):
    data, err = _parse_json_body(request)
    if err:
        return err
    limited = _too_many(request)
    if limited:
        return limited

    username = str(data.get('username', '')).strip()
    password = str(data.get('password', '')).strip()
    recovery_key = str(data.get('recovery_key', '')).strip().lower()[:120]

    if len(username) < 2 or len(username) > 60:
        _record(request, data, 'register', False, 'invalid_username')
        return JsonResponse({'success': False, 'message': '아이디는 2~60자로 입력해주세요.'}, status=400)
    if username.lower() == 'guest':
        _record(request, data, 'register', False, 'reserved_name')
        return JsonResponse({'success': False, 'message': 'Guest는 예약된 이름입니다.'}, status=400)
    if len(password) < 3:
        _record(request, data, 'register', False, 'weak_password')
        return JsonResponse({'success': False, 'message': '비밀번호는 3글자 이상 입력해주세요.'}, status=400)

    if GameAccount.objects.filter(username=username).exists():
        _record(request, data, 'register', False, 'username_taken')
        return JsonResponse({'success': False, 'message': '이미 사용 중인 아이디입니다.'}, status=409)

    save_data = _default_save_data()
    with transaction.atomic():
        member_uuid = str(uuid.uuid4())
        player = Player.objects.create(
            external_id=f'game:member:{member_uuid}',
            display_name=username[:80],
            source='live',
        )
        account = GameAccount.objects.create(
            player=player,
            username=username,
            password_hash=make_password(password),
            recovery_key=recovery_key,
            save_data=save_data,
        )
    _record(request, data, 'register', True, account=account)

    return JsonResponse({
        'success': True,
        'message': '회원가입이 완료되었습니다! (클라우드 DB 저장 완료)',
        'username': account.username,
        'player_id': str(account.player_id),
        'save_data': account.save_data,
    }, status=201)


@csrf_exempt
@never_cache
def game_auth_login(request):
    data, err = _parse_json_body(request)
    if err:
        return err
    limited = _too_many(request)
    if limited:
        return limited

    username = str(data.get('username', '')).strip()
    password = str(data.get('password', '')).strip()
    if not username or not password:
        return JsonResponse({'success': False, 'message': '아이디와 비밀번호를 모두 입력해주세요.'}, status=400)

    fail_key = _fail_key(username)
    if (cache.get(fail_key) or 0) >= FAILURE_LIMIT[0]:
        _record(request, data, 'login', False, 'locked')
        return JsonResponse({'success': False, 'message': '로그인 실패가 많아 10분간 잠겼습니다. 잠시 후 다시 시도해주세요.'}, status=429)

    account = GameAccount.objects.select_related('player').filter(username=username).first()
    if account is None:
        check_password(password, _DUMMY_HASH)  # same cost as a real check
        _bump(fail_key, FAILURE_LIMIT)
        _record(request, data, 'login', False, 'unknown_username')
        return JsonResponse({'success': False, 'message': '존재하지 않는 아이디입니다.'}, status=401)
    if not check_password(password, account.password_hash):
        _bump(fail_key, FAILURE_LIMIT)
        _record(request, data, 'login', False, 'wrong_password', account=account)
        return JsonResponse({'success': False, 'message': '비밀번호가 일치하지 않습니다.'}, status=401)

    cache.delete(fail_key)
    account.last_login = timezone.now()
    account.save(update_fields=['last_login'])
    _record(request, data, 'login', True, account=account)

    save_data = account.save_data if isinstance(account.save_data, dict) else _default_save_data()
    return JsonResponse({
        'success': True,
        'message': '로그인 성공! 클라우드 저장 데이터를 불러왔습니다.',
        'username': account.username,
        'player_id': str(account.player_id),
        'save_data': save_data,
    }, status=200)


@csrf_exempt
@never_cache
def game_auth_find_id(request):
    data, err = _parse_json_body(request)
    if err:
        return err
    limited = _too_many(request)
    if limited:
        return limited

    recovery_key = str(data.get('recovery_key', '')).strip().lower()
    if not recovery_key:
        return JsonResponse({'success': False, 'usernames': [], 'message': '복구용 이메일 또는 별명을 입력해주세요.'}, status=400)

    usernames = list(GameAccount.objects.filter(recovery_key=recovery_key).values_list('username', flat=True)[:10])
    if not usernames:
        _record(request, data, 'find_id', False, 'not_found', username='')
        return JsonResponse({'success': False, 'usernames': [], 'message': '일치하는 계정을 찾을 수 없습니다.'}, status=404)
    _record(request, data, 'find_id', True, username=', '.join(usernames))

    return JsonResponse({
        'success': True,
        'usernames': usernames,
        'message': f"찾은 아이디: {', '.join(usernames)}",
    }, status=200)


@csrf_exempt
@never_cache
def game_auth_reset_password(request):
    data, err = _parse_json_body(request)
    if err:
        return err
    limited = _too_many(request)
    if limited:
        return limited

    username = str(data.get('username', '')).strip()
    recovery_key = str(data.get('recovery_key', '')).strip().lower()
    new_password = str(data.get('new_password', '')).strip()

    if not username:
        return JsonResponse({'success': False, 'message': '아이디를 입력해주세요.'}, status=400)
    if len(new_password) < 3:
        return JsonResponse({'success': False, 'message': '새 비밀번호는 3글자 이상 입력해주세요.'}, status=400)

    fail_key = _fail_key(username)
    if (cache.get(fail_key) or 0) >= FAILURE_LIMIT[0]:
        _record(request, data, 'reset', False, 'locked')
        return JsonResponse({'success': False, 'message': '시도가 너무 많아 10분간 잠겼습니다. 잠시 후 다시 시도해주세요.'}, status=429)

    account = GameAccount.objects.select_related('player').filter(username=username).first()
    if account is None:
        _record(request, data, 'reset', False, 'unknown_username')
        return JsonResponse({'success': False, 'message': '존재하지 않는 아이디입니다.'}, status=404)

    # Without a registered recovery key anyone could take the account over, so it is required.
    if not account.recovery_key:
        _record(request, data, 'reset', False, 'no_recovery_key', account=account)
        return JsonResponse({'success': False, 'message': '복구용 이메일/별명이 등록되지 않은 계정입니다. 관리자에게 문의해주세요.'}, status=403)
    if account.recovery_key != recovery_key:
        _bump(fail_key, FAILURE_LIMIT)
        _record(request, data, 'reset', False, 'wrong_recovery_key', account=account)
        return JsonResponse({'success': False, 'message': '복구용 이메일/별명이 일치하지 않습니다.'}, status=403)

    account.password_hash = make_password(new_password)
    account.save(update_fields=['password_hash'])
    cache.delete(fail_key)
    _record(request, data, 'reset', True, account=account)

    return JsonResponse({
        'success': True,
        'message': '비밀번호가 안전하게 변경되었습니다! 새 비밀번호로 로그인하세요.',
    }, status=200)


@csrf_exempt
@never_cache
def game_auth_save(request):
    data, err = _parse_json_body(request)
    if err:
        return err

    username = str(data.get('username', '')).strip()
    save_data = data.get('save_data')
    if not username or not isinstance(save_data, dict):
        return JsonResponse({'success': False, 'message': '유효한 계정과 저장 데이터가 필요합니다.'}, status=400)

    account = GameAccount.objects.filter(username=username).first()
    if account is None:
        return JsonResponse({'success': False, 'message': '계정을 찾을 수 없습니다.'}, status=404)

    save_data['last_saved'] = timezone.now().isoformat()
    account.save_data = save_data
    account.save(update_fields=['save_data'])
    return JsonResponse({'success': True, 'message': '클라우드 저장 완료'}, status=200)
