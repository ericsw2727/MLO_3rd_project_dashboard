import os
from pathlib import Path
from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

def required(name):
    value = os.getenv(name)
    if not value:
        raise ImproperlyConfigured(f'{name} 환경변수가 필요합니다. .env.example을 확인하세요.')
    return value

SECRET_KEY = required('DJANGO_SECRET_KEY')
ADMIN_REGISTRATION_CODE = os.getenv('ADMIN_REGISTRATION_CODE', '')
DEBUG = os.getenv('DJANGO_DEBUG', 'False').lower() == 'true'
ALLOWED_HOSTS = os.getenv('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
INSTALLED_APPS = ['django.contrib.auth', 'django.contrib.contenttypes', 'django.contrib.sessions', 'django.contrib.staticfiles', 'accounts', 'telemetry']
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
]
ROOT_URLCONF = 'config.urls'
TEMPLATES = [{'BACKEND': 'django.template.backends.django.DjangoTemplates', 'DIRS': [BASE_DIR / 'templates'], 'APP_DIRS': True,
              'OPTIONS': {'context_processors': ['django.template.context_processors.request', 'django.contrib.auth.context_processors.auth']}}]
WSGI_APPLICATION = 'config.wsgi.application'
DATABASES = {'default': {
    'ENGINE': 'django.db.backends.mysql', 'NAME': required('MYSQL_DATABASE'),
    'USER': required('MYSQL_USER'), 'PASSWORD': required('MYSQL_PASSWORD'),
    'HOST': required('MYSQL_HOST'), 'PORT': required('MYSQL_PORT'),
    'OPTIONS': {'charset': 'utf8mb4', 'init_command': "SET sql_mode='STRICT_TRANS_TABLES'"},
    'TEST': {'NAME': os.getenv('MYSQL_TEST_DATABASE', 'test_nodeverse')},
}}
if DATABASES['default']['TEST']['NAME'] == DATABASES['default']['NAME']:
    raise ImproperlyConfigured('MYSQL_TEST_DATABASE는 개발 DB와 다른 전용 테스트 DB여야 합니다.')
AUTH_USER_MODEL = 'accounts.User'
AUTHENTICATION_BACKENDS = ['accounts.backends.AdminBackend']
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
LANGUAGE_CODE = 'ko-kr'
TIME_ZONE = 'Asia/Seoul'
USE_TZ = True
LOGIN_URL = '/staff/login/'
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_AGE = 60 * 60 * 8
CSRF_FAILURE_VIEW = 'accounts.views.csrf_failure'
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
