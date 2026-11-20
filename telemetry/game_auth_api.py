"""Game client player authentication & cloud save API backed by MySQL (game_accounts + game_members)."""
import json
import uuid

from django.contrib.auth.hashers import make_password, check_password
from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt

from .models import Player, GameAccount


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


@csrf_exempt
@never_cache
def game_auth_register(request):
    data, err = _parse_json_body(request)
    if err:
        return err

    username = str(data.get('username', '')).strip()
    password = str(data.get('password', '')).strip()
    recovery_key = str(data.get('recovery_key', '')).strip().lower()[:120]

    if len(username) < 2 or len(username) > 60:
        return JsonResponse({'success': False, 'message': '아이디는 2~60자로 입력해주세요.'}, status=400)
    if username.lower() == 'guest':
        return JsonResponse({'success': False, 'message': 'Guest는 예약된 이름입니다.'}, status=400)
    if len(password) < 3:
        return JsonResponse({'success': False, 'message': '비밀번호는 3글자 이상 입력해주세요.'}, status=400)

    if GameAccount.objects.filter(username=username).exists():
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

    username = str(data.get('username', '')).strip()
    password = str(data.get('password', '')).strip()
    if not username or not password:
        return JsonResponse({'success': False, 'message': '아이디와 비밀번호를 모두 입력해주세요.'}, status=400)

    account = GameAccount.objects.select_related('player').filter(username=username).first()
    if account is None:
        return JsonResponse({'success': False, 'message': '존재하지 않는 아이디입니다.'}, status=401)
    if not check_password(password, account.password_hash):
        return JsonResponse({'success': False, 'message': '비밀번호가 일치하지 않습니다.'}, status=401)

    account.last_login = timezone.now()
    account.save(update_fields=['last_login'])

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

    recovery_key = str(data.get('recovery_key', '')).strip().lower()
    if not recovery_key:
        return JsonResponse({'success': False, 'usernames': [], 'message': '복구용 이메일 또는 별명을 입력해주세요.'}, status=400)

    usernames = list(GameAccount.objects.filter(recovery_key=recovery_key).values_list('username', flat=True)[:10])
    if not usernames:
        return JsonResponse({'success': False, 'usernames': [], 'message': '일치하는 계정을 찾을 수 없습니다.'}, status=404)

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

    username = str(data.get('username', '')).strip()
    recovery_key = str(data.get('recovery_key', '')).strip().lower()
    new_password = str(data.get('new_password', '')).strip()

    if not username:
        return JsonResponse({'success': False, 'message': '아이디를 입력해주세요.'}, status=400)
    if len(new_password) < 3:
        return JsonResponse({'success': False, 'message': '새 비밀번호는 3글자 이상 입력해주세요.'}, status=400)

    account = GameAccount.objects.filter(username=username).first()
    if account is None:
        return JsonResponse({'success': False, 'message': '존재하지 않는 아이디입니다.'}, status=404)

    if account.recovery_key and account.recovery_key != recovery_key:
        return JsonResponse({'success': False, 'message': '복구용 이메일/별명이 일치하지 않습니다.'}, status=403)

    account.password_hash = make_password(new_password)
    if not account.recovery_key and recovery_key:
        account.recovery_key = recovery_key[:120]
    account.save(update_fields=['password_hash', 'recovery_key'])

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
