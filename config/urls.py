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
from telemetry import releases, live

urlpatterns = [
    path('api/game/records', game_records, name='game-records'),
    path('api/game/player-login', player_login, name='game-player-login'),
    path('api/game/auth/register', game_auth_register, name='game-auth-register'),
    path('api/game/auth/login', game_auth_login, name='game-auth-login'),
    path('api/game/auth/find-id', game_auth_find_id, name='game-auth-find-id'),
    path('api/game/auth/reset-password', game_auth_reset_password, name='game-auth-reset-password'),
    path('api/game/auth/save', game_auth_save, name='game-auth-save'),
    # Game client: updates (public, read-only).
    path('api/game/manifest', releases.manifest, name='game-manifest'),
    path('downloads/packs/<str:filename>', releases.pack_file, name='pack-file'),
    path('downloads/builds/<int:release_id>/', releases.build_file, name='build-file'),
    path('download/', releases.download_page, name='download'),
    path('', require_GET(TemplateView.as_view(template_name='portal/index.html')), name='home'),
    path('index.html', require_GET(RedirectView.as_view(pattern_name='home', permanent=False))),
    path('dashboard.html', require_GET(RedirectView.as_view(pattern_name='dashboard', permanent=False))),
    path('staff/', analytics.dashboard_page, name='dashboard'),
    path('staff/games/', analytics.dashboard_page, {'scope': 'game'}, name='games'),
    path('staff/players/', analytics.players_page, name='players'),
    path('staff/players/<uuid:player_id>/', analytics.player_page, name='player-detail'),
    path('staff/events/', analytics.events_page, name='events'),
    path('staff/guide/', analytics.guide_page, name='guide'),
    path('staff/live/', live.live_page, name='live'),
    path('staff/members/', live.members_page, name='members'),
    path('staff/members/<uuid:player_id>/', live.member_detail_page, name='member-detail'),
    path('staff/download/', releases.download_admin_page, name='download-tab'),
    path('staff/releases/', releases.releases_page, name='releases'),
    path('staff/releases/<int:release_id>/toggle/', releases.toggle_release, name='release-toggle'),
    path('staff/releases/packs/<int:pack_id>/toggle/', releases.toggle_pack, name='pack-toggle'),
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
    path('api/admin/live/summary', live.summary_api),
    path('api/admin/live/minigames', live.minigames_api),
    path('api/admin/live/alerts', live.alerts_api),
    path('api/admin/live/updates', live.updates_api),
]
