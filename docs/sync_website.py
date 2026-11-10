"""Build Django's public template/scripts from the team's website/ source.

Run after updating website/. Binary assets are served from that source directly
via the named Django staticfiles directory; no duplicate videos/images required.
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / 'website'
TARGET = ROOT / 'static' / 'portal'


def build():
    TARGET.mkdir(parents=True, exist_ok=True)
    html = (SOURCE / 'index.html').read_text(encoding='utf-8-sig')
    def asset(match):
        attr, url = match.groups()
        target = '/' if url == 'index.html' else '/staff/' if url == 'dashboard.html' else '/static/portal/' + url
        return f'{attr}="{target}"'
    html = re.sub(r'(src|href|poster)="(?!https?:|#|/)([^"]+)"', asset, html)
    html = html.replace('<a href="#film">소개 영상</a>', '<a href="#film">소개 영상</a>\n      <a href="/staff/">관리자 로그인</a>')
    template = ROOT / 'templates' / 'portal' / 'index.html'
    template.parent.mkdir(parents=True, exist_ok=True)
    template.write_text(html, encoding='utf-8')
    for path in SOURCE.iterdir():
        if path.suffix not in ('.js', '.css') or path.name == 'dashboard.js':
            continue
        text = path.read_text(encoding='utf-8-sig')
        if path.suffix == '.js':
            text = text.replace('assets/', '/static/portal/assets/')
        (TARGET / path.name).write_text(text, encoding='utf-8')
    print('Built public template and scripts from website/; administrator routes preserved.')


if __name__ == '__main__':
    build()
