import json
from functools import wraps
from django.contrib.auth import login, logout
from django.http import JsonResponse, HttpResponseForbidden
from django.middleware.csrf import get_token
from django.shortcuts import render, redirect
from django.views.decorators.cache import never_cache
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_GET, require_POST
from .forms import AdminRegisterForm, AdminLoginForm
from .services import register_admin_account, admin_account_data
from .development import local_test_login_allowed, TEST_ADMIN_ID, TEST_ADMIN_USERNAME


def csrf_failure(request, reason=''):
    if request.path.startswith('/api/'):
        return JsonResponse({'error': 'csrf_failed'}, status=403)
    return HttpResponseForbidden('CSRF 검증에 실패했습니다. 페이지를 새로고침하세요.')


def api(method, authenticated=False):
    def decorate(view):
        @wraps(view)
        @never_cache
        def wrapped(request, *args, **kwargs):
            if request.method != method:
                response = JsonResponse({'error': 'method_not_allowed'}, status=405)
                response['Allow'] = method
                return response
            if authenticated and not request.user.is_authenticated:
                return JsonResponse({'error': 'authentication_required'}, status=401)
            if authenticated and request.user.role != 'admin':
                return JsonResponse({'error': 'permission_denied'}, status=403)
            return view(request, *args, **kwargs)
        return wrapped
    return decorate


def json_data(request):
    if request.content_type != 'application/json':
        return None, JsonResponse({'error': 'application_json_required'}, status=415)
    try:
        request_data = json.loads(request.body)
        if not isinstance(request_data, dict) or any(not isinstance(v, str) for v in request_data.values()):
            raise ValueError
        return request_data, None
    except (ValueError, UnicodeDecodeError):
        return None, JsonResponse({'error': 'invalid_json'}, status=400)


@api('GET')
def csrf_api(request):
    return JsonResponse({'csrf_token': get_token(request)})


@api('POST')
def register_api(request):
    request_data, error = json_data(request)
    if error is not None:
        return error
    admin_account, admin_form = register_admin_account({'username': request_data.get('login_id', ''), 'display_name': request_data.get('display_name', ''),
                           'password1': request_data.get('password', ''), 'password2': request_data.get('password_confirm', ''),
                           'invitation_code': request_data.get('invitation_code', '')})
    if admin_account is None:
        return JsonResponse({'errors': admin_form.errors.get_json_data()}, status=400)
    return JsonResponse({'user': admin_account_data(admin_account)}, status=201)


@api('POST')
def login_api(request):
    request_data, error = json_data(request)
    if error is not None:
        return error
    admin_form = AdminLoginForm(request, data={'username': request_data.get('login_id', ''), 'password': request_data.get('password', '')})
    if not admin_form.is_valid():
        return JsonResponse({'error': 'invalid_credentials'}, status=401)
    login(request, admin_form.get_user())
    return JsonResponse({'user': admin_account_data(request.user), 'csrf_token': get_token(request)})


@api('GET', authenticated=True)
def me_api(request):
    return JsonResponse({'user': admin_account_data(request.user)})


@api('POST', authenticated=True)
def logout_api(request):
    _, error = json_data(request)
    if error is not None:
        return error
    logout(request)
    return JsonResponse({'detail': 'logged_out'})


@sensitive_post_parameters('password1', 'password2', 'invitation_code')
@never_cache
def admin_register_page(request):
    if request.method not in ('GET', 'POST'):
        return JsonResponse({'error': 'method_not_allowed'}, status=405)
    admin_form = AdminRegisterForm()
    if request.method == 'POST':
        admin_account, admin_form = register_admin_account(request.POST)
        if admin_account:
            return redirect('admin-login')
    return render(request, 'accounts/form.html', {'form': admin_form, 'title': '관리자 계정 만들기', 'is_register': True})


@sensitive_post_parameters('password')
@never_cache
def admin_login_page(request):
    if request.method not in ('GET', 'POST'):
        return JsonResponse({'error': 'method_not_allowed'}, status=405)
    admin_form = AdminLoginForm(request, data=request.POST if request.method == 'POST' else None)
    if request.method == 'POST' and admin_form.is_valid():
        login(request, admin_form.get_user())
        return redirect('dashboard')
    return render(request, 'accounts/form.html', {'form': admin_form, 'title': '관리자 로그인',
                                                'show_test_login': local_test_login_allowed(request)})


@require_POST
@never_cache
def test_admin_login(request):
    if not local_test_login_allowed(request):
        return HttpResponseForbidden('로컬 개발 환경에서만 사용할 수 있습니다.')
    from django.contrib.auth import get_user_model
    from django.contrib.auth.hashers import make_password
    from django.db import IntegrityError
    try:
        admin_account, _ = get_user_model().objects.get_or_create(pk=TEST_ADMIN_ID, defaults={
            'username': TEST_ADMIN_USERNAME, 'display_name': '테스트 관리자', 'role': 'admin',
            'password': make_password(None), 'is_staff': False, 'is_superuser': False,
        })
    except IntegrityError:
        return HttpResponseForbidden('테스트 계정 이름이 기존 계정과 충돌합니다.')
    if (admin_account.username != TEST_ADMIN_USERNAME or admin_account.role != 'admin'
            or not admin_account.is_active or admin_account.has_usable_password()):
        return HttpResponseForbidden('테스트 계정 상태를 확인해 주세요.')
    login(request, admin_account, backend='accounts.backends.AdminBackend')
    request.session.set_expiry(60 * 60)
    return redirect('dashboard')


def admin_page(view):
    @wraps(view)
    @never_cache
    def wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('admin-login')
        if request.user.role != 'admin':
            return HttpResponseForbidden('관리자만 접근할 수 있습니다.')
        return view(request, *args, **kwargs)
    return wrapped


@require_GET
@admin_page
def me_page(request):
    return render(request, 'accounts/me.html')


@require_POST
@admin_page
def logout_page(request):
    logout(request)
    return redirect('admin-login')
