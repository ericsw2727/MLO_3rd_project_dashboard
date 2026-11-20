from django.urls import path
from django.views.generic import RedirectView, TemplateView
from django.views.decorators.http import require_GET
from accounts import views
from telemetry import views as analytics
from telemetry.game_api import player_login, game_records
from telemetry.game_auth_api import (
    game_auth_register,
    game_auth_login,
    game_auth_find_id,
    game_auth_reset_password,
    game_auth_save,
)

urlpatterns = [
    path('api/game/records', game_records, name='game-records'),
    path('api/game/player-login', player_login, name='game-player-login'),
    path('api/game/auth/register', game_auth_register, name='game-auth-register'),
    path('api/game/auth/login', game_auth_login, name='game-auth-login'),
    path('api/game/auth/find-id', game_auth_find_id, name='game-auth-find-id'),
    path('api/game/auth/reset-password', game_auth_reset_password, name='game-auth-reset-password'),
    path('api/game/auth/save', game_auth_save, name='game-auth-save'),
    path('', require_GET(TemplateView.as_view(template_name='portal/index.html')), name='home'),
    path('index.html', require_GET(RedirectView.as_view(pattern_name='home', permanent=False))),
    path('dashboard.html', require_GET(RedirectView.as_view(pattern_name='dashboard', permanent=False))),
    path('staff/', analytics.dashboard_page, name='dashboard'),
    path('staff/games/', analytics.dashboard_page, {'scope': 'game'}, name='games'),
    path('staff/players/', analytics.players_page, name='players'),
    path('staff/players/<uuid:player_id>/', analytics.player_page, name='player-detail'),
    path('staff/events/', analytics.events_page, name='events'),
    path('staff/guide/', analytics.guide_page, name='guide'),
    path('staff/export/', analytics.export_runs, name='export'),
    path('staff/register/', views.admin_register_page, name='admin-register'),
    path('staff/login/', views.admin_login_page, name='admin-login'),
    path('staff/test-login/', views.test_admin_login, name='test-admin-login'),
    path('login/', require_GET(RedirectView.as_view(pattern_name='admin-login', permanent=False))),
    path('register/', require_GET(RedirectView.as_view(pattern_name='admin-register', permanent=False))),
    path('me/', views.me_page, name='me'),
    path('logout/', views.logout_page, name='logout'),
    path('admin-check/', analytics.dashboard_page),
    path('api/auth/csrf', views.csrf_api),
    path('api/auth/register', views.register_api),
    path('api/auth/login', views.login_api),
    path('api/auth/me', views.me_api),
    path('api/auth/logout', views.logout_api),
    path('api/admin/me', views.me_api),
    path('api/admin/summary', analytics.summary_api),
    path('api/admin/visuals', analytics.visuals_api),
    path('api/admin/players', analytics.players_api),
    path('api/admin/players/<uuid:player_id>', analytics.player_api),
    path('api/admin/events', analytics.events_api),
]
