"""S5 game update interface: public manifest + pack files, admin-only registration.

The game reads GET /api/game/manifest once at boot. Only reading the manifest and
pack files is public; registering and (de)activating is for administrators.
"""
import hashlib
import json
import re
from pathlib import PurePosixPath

from django import forms
from django.conf import settings
from django.contrib import messages
from django.db import IntegrityError
from django.http import FileResponse, Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST

from accounts.views import admin_page
from .models import ContentPack, GameRelease

BUILD_RE = re.compile(r'^\d{1,4}\.\d{1,4}\.\d{1,4}$')
PACK_VERSION_RE = re.compile(r'^[A-Za-z0-9][A-Za-z0-9._-]{0,39}$')
CHANNEL_RE = re.compile(r'^[a-z0-9][a-z0-9-]{0,29}$')
DEFAULT_CHANNEL = 'windows-stable'


def build_key(version):
    """주.부.수 numeric comparison key; invalid versions sort lowest."""
    try:
        return tuple(int(part) for part in str(version).split('.'))
    except ValueError:
        return (-1,)


def absolute(request, path):
    base = settings.PUBLIC_BASE_URL
    return base + path if base else request.build_absolute_uri(path)


def active_release(channel=DEFAULT_CHANNEL):
    releases = list(GameRelease.objects.filter(channel=channel, is_active=True))
    return max(releases, key=lambda r: (build_key(r.build_version), r.published_at), default=None)


def active_pack():
    return ContentPack.objects.filter(is_active=True).order_by('-uploaded_at', '-pk').first()


def pack_url(request, pack):
    return absolute(request, '/downloads/packs/' + PurePosixPath(pack.file.name).name)


def build_manifest(request, channel):
    release = active_release(channel)
    if release is None:
        return None
    pack = active_pack()
    return {
        'channel': channel,
        'latest_build': release.build_version,
        'min_build': release.min_build,
        'download_page': release.download_page or absolute(request, '/download/'),
        'notes': release.notes,
        'content': {
            'version': pack.version if pack else 'base',
            'packs': [{'file': PurePosixPath(pack.file.name).name, 'url': pack_url(request, pack),
                       'sha256': pack.sha256, 'size': pack.size, 'min_build': pack.min_build}] if pack else [],
        },
    }


@require_GET
def manifest(request):
    channel = request.GET.get('channel', DEFAULT_CHANNEL)
    if not CHANNEL_RE.match(channel):
        return JsonResponse({'error': 'invalid_channel'}, status=400)
    data = build_manifest(request, channel)
    if data is None:
        response = JsonResponse({'error': 'no_active_release', 'channel': channel}, status=404)
        response['Cache-Control'] = 'no-store'
        return response
    body = json.dumps(data, ensure_ascii=False, sort_keys=True).encode('utf-8')
    etag = '"' + hashlib.sha256(body).hexdigest()[:32] + '"'
    if etag in [tag.strip() for tag in request.headers.get('If-None-Match', '').split(',')]:
        response = HttpResponse(status=304)
    else:
        response = HttpResponse(body, content_type='application/json; charset=utf-8')
    response['ETag'] = etag
    response['Cache-Control'] = 'public, max-age=60'
    return response


@require_GET
def pack_file(request, filename):
    pack = next((p for p in ContentPack.objects.all() if PurePosixPath(p.file.name).name == filename), None)
    if pack is None or not pack.file.storage.exists(pack.file.name):
        raise Http404('pack not found')
    response = FileResponse(pack.file.open('rb'), content_type='application/octet-stream',
                            as_attachment=True, filename=filename)
    # File names include the version, so content never changes.
    response['Cache-Control'] = 'public, max-age=31536000, immutable'
    return response


@require_GET
def build_file(request, release_id):
    release = get_object_or_404(GameRelease, pk=release_id, is_active=True)
    if not release.package:
        raise Http404('no package')
    return FileResponse(release.package.open('rb'), as_attachment=True,
                        filename=PurePosixPath(release.package.name).name)


@require_GET
def download_page(request):
    release = active_release(request.GET.get('channel', DEFAULT_CHANNEL) if CHANNEL_RE.match(
        request.GET.get('channel', DEFAULT_CHANNEL)) else DEFAULT_CHANNEL)
    link = None
    if release:
        link = release.package_url or (f'/downloads/builds/{release.pk}/' if release.package else None)
    return render(request, 'releases/download.html', {'release': release, 'link': link, 'pack': active_pack()})


def release_link(release):
    if release.package_url:
        return release.package_url
    return f'/downloads/builds/{release.pk}/' if release.package else None


@require_GET
@admin_page
def download_admin_page(request):
    """Dashboard tab: what players download right now, plus the links to hand out."""
    release, pack = active_release(), active_pack()
    history = sorted(GameRelease.objects.filter(channel=DEFAULT_CHANNEL),
                     key=lambda r: (build_key(r.build_version), r.published_at), reverse=True)[:10]
    for item in history:
        item.link = release_link(item) if item.is_active else None
        item.size = item.package.size if item.package and item.package.storage.exists(item.package.name) else None
    manifest_path = '/api/game/manifest?channel=' + DEFAULT_CHANNEL
    return render(request, 'releases/download_tab.html', {
        'release': release, 'pack': pack, 'link': release_link(release) if release else None,
        'history': history,
        'links': [
            {'label': '공개 다운로드 페이지', 'help': '플레이어에게 공유하는 주소. 매니페스트의 download_page',
             'url': (release.download_page if release and release.download_page else absolute(request, '/download/'))},
            {'label': '업데이트 매니페스트', 'help': '게임 설정에 넣는 주소. 시작할 때 한 번 읽음',
             'url': absolute(request, manifest_path)},
            {'label': '게임 서버 주소', 'help': '로그인 API와 매니페스트의 기준 주소',
             'url': absolute(request, '/').rstrip('/')},
        ] + ([{'label': '현재 리소스 팩', 'help': f'{pack.version} · SHA-256 {pack.sha256[:16]}…',
               'url': pack_url(request, pack)}] if pack else []),
    })


# ---------- administrator registration (/staff/releases/) ----------

class ReleaseForm(forms.ModelForm):
    class Meta:
        model = GameRelease
        fields = ['channel', 'build_version', 'min_build', 'notes', 'download_page', 'package_url', 'package']
        labels = {'channel': '채널', 'build_version': 'EXE 버전', 'min_build': '최소 빌드(필수 업데이트 기준)',
                  'notes': '변경 내용', 'download_page': '다운로드 페이지 (비우면 /download/)',
                  'package_url': '외부 EXE ZIP 주소 (선택)', 'package': 'EXE ZIP 업로드 (선택)'}

    def clean_channel(self):
        value = self.cleaned_data['channel']
        if not CHANNEL_RE.match(value):
            raise forms.ValidationError('소문자·숫자·하이픈만 사용합니다.')
        return value

    def clean(self):
        data = super().clean()
        for name in ('build_version', 'min_build'):
            if data.get(name) and not BUILD_RE.match(data[name]):
                self.add_error(name, '주.부.수 숫자 형식이어야 합니다. 예: 0.3.1')
        if data.get('build_version') and data.get('min_build') and BUILD_RE.match(data['build_version']) \
                and BUILD_RE.match(data['min_build']) and build_key(data['min_build']) > build_key(data['build_version']):
            self.add_error('min_build', '최소 빌드는 EXE 버전보다 높을 수 없습니다.')
        return data


class PackForm(forms.Form):
    version = forms.CharField(label='팩 버전', max_length=40, help_text='예: content-2026.11.19')
    min_build = forms.CharField(label='필요 최소 빌드', max_length=20, help_text='예: 0.3.0')
    file = forms.FileField(label='.pck 파일')

    def clean_version(self):
        value = self.cleaned_data['version']
        if not PACK_VERSION_RE.match(value):
            raise forms.ValidationError('영문·숫자·.-_ 만 사용합니다.')
        if ContentPack.objects.filter(version=value).exists():
            raise forms.ValidationError('이미 등록된 버전입니다. 팩 내용은 바꿀 수 없으니 새 버전으로 올리세요.')
        return value

    def clean_min_build(self):
        value = self.cleaned_data['min_build']
        if not BUILD_RE.match(value):
            raise forms.ValidationError('주.부.수 숫자 형식이어야 합니다.')
        return value

    def clean_file(self):
        upload = self.cleaned_data['file']
        if not upload.name.lower().endswith('.pck'):
            raise forms.ValidationError('.pck 파일만 올릴 수 있습니다.')
        return upload


def save_pack(version, min_build, upload):
    """Hash and size come from the uploaded bytes, never from user input."""
    digest = hashlib.sha256()
    size = 0
    for chunk in upload.chunks():
        digest.update(chunk)
        size += len(chunk)
    upload.seek(0)
    pack = ContentPack(version=version, min_build=min_build, sha256=digest.hexdigest(), size=size)
    pack.file.save(f'{version}.pck', upload, save=False)
    pack.save()
    return pack


@admin_page
def releases_page(request):
    release_form, pack_form = ReleaseForm(prefix='release'), PackForm(prefix='pack')
    if request.method == 'POST':
        if request.POST.get('form') == 'release':
            release_form = ReleaseForm(request.POST, request.FILES, prefix='release')
            if release_form.is_valid():
                try:
                    release_form.save()
                    messages.success(request, '릴리스를 등록했습니다. 1분 안에 매니페스트에 반영됩니다.')
                    return redirect('releases')
                except IntegrityError:
                    release_form.add_error('build_version', '같은 채널에 이미 있는 버전입니다.')
        elif request.POST.get('form') == 'pack':
            pack_form = PackForm(request.POST, request.FILES, prefix='pack')
            if pack_form.is_valid():
                data = pack_form.cleaned_data
                pack = save_pack(data['version'], data['min_build'], data['file'])
                messages.success(request, f'팩 {pack.version}을 등록했습니다 (SHA-256 {pack.sha256[:12]}…).')
                return redirect('releases')
    releases = sorted(GameRelease.objects.all(), key=lambda r: (r.channel, build_key(r.build_version)), reverse=True)
    current = {r.channel: active_release(r.channel) for r in releases}
    return render(request, 'releases/manage.html', {
        'release_form': release_form, 'pack_form': pack_form, 'releases': releases,
        'serving_release_ids': {r.pk for r in current.values() if r},
        'packs': ContentPack.objects.order_by('-uploaded_at', '-pk'), 'serving_pack': active_pack(),
        'manifest_url': '/api/game/manifest?channel=' + DEFAULT_CHANNEL,
    })


@require_POST
@admin_page
def toggle_release(request, release_id):
    release = get_object_or_404(GameRelease, pk=release_id)
    release.is_active = not release.is_active
    release.save(update_fields=['is_active'])
    messages.success(request, f'릴리스 {release.build_version}을 {"활성화" if release.is_active else "비활성화"}했습니다.')
    return redirect('releases')


@require_POST
@admin_page
def toggle_pack(request, pack_id):
    pack = get_object_or_404(ContentPack, pk=pack_id)
    pack.is_active = not pack.is_active
    pack.save(update_fields=['is_active'])
    messages.success(request, f'팩 {pack.version}을 {"활성화" if pack.is_active else "비활성화"}했습니다. 파일은 지우지 않습니다.')
    return redirect('releases')
