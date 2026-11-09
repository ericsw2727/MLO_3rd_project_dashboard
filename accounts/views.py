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
from .services import register, user_data


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
        data = json.loads(request.body)
        if not isinstance(data, dict) or any(not isinstance(v, str) for v in data.values()):
            raise ValueError
        return data, None
    except (ValueError, UnicodeDecodeError):
        return None, JsonResponse({'error': 'invalid_json'}, status=400)


@api('GET')
def csrf_api(request):
    return JsonResponse({'csrf_token': get_token(request)})


@api('POST')
def register_api(request):
    data, error = json_data(request)
    if error is not None:
        return error
    user, form = register({'username': data.get('login_id', ''), 'display_name': data.get('display_name', ''),
                           'password1': data.get('password', ''), 'password2': data.get('password_confirm', ''),
                           'invitation_code': data.get('invitation_code', '')})
    if user is None:
        return JsonResponse({'errors': form.errors.get_json_data()}, status=400)
    return JsonResponse({'user': user_data(user)}, status=201)


@api('POST')
def login_api(request):
    data, error = json_data(request)
    if error is not None:
        return error
    form = AdminLoginForm(request, data={'username': data.get('login_id', ''), 'password': data.get('password', '')})
    if not form.is_valid():
        return JsonResponse({'error': 'invalid_credentials'}, status=401)
    login(request, form.get_user())
    return JsonResponse({'user': user_data(request.user), 'csrf_token': get_token(request)})


@api('GET', authenticated=True)
def me_api(request):
    return JsonResponse({'user': user_data(request.user)})


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
    form = AdminRegisterForm()
    if request.method == 'POST':
        user, form = register(request.POST)
        if user:
            return redirect('admin-login')
    return render(request, 'accounts/form.html', {'form': form, 'title': '관리자 계정 만들기', 'is_register': True})


@sensitive_post_parameters('password')
@never_cache
def admin_login_page(request):
    if request.method not in ('GET', 'POST'):
        return JsonResponse({'error': 'method_not_allowed'}, status=405)
    form = AdminLoginForm(request, data=request.POST if request.method == 'POST' else None)
    if request.method == 'POST' and form.is_valid():
        login(request, form.get_user())
        return redirect('dashboard')
    return render(request, 'accounts/form.html', {'form': form, 'title': '관리자 로그인'})


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
