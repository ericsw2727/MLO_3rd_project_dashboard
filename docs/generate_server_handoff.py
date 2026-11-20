"""Team handoff PDF for the server part (changes and progress). Run: python docs/generate_server_handoff.py"""
from pathlib import Path
import html

from reportlab.lib.colors import HexColor
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output/pdf'
FILENAME = 'NODEVERSE_서버파트_변경사항_진행상황.pdf'
STAMP = 'NODEVERSE / 서버 파트 / 2026.11.20'

pdfmetrics.registerFont(TTFont('KR', 'C:/Windows/Fonts/malgun.ttf'))
pdfmetrics.registerFont(TTFont('KRB', 'C:/Windows/Fonts/malgunbd.ttf'))
INK, ACCENT, MUTED, LINE, SOFT = '#173d35', '#176b57', '#6f8177', '#dce5e0', '#edf3f0'
S = {
    'title': ParagraphStyle('title', fontName='KRB', fontSize=21, leading=30, spaceAfter=10, textColor=HexColor(INK), wordWrap='CJK'),
    'h': ParagraphStyle('h', fontName='KRB', fontSize=12.5, leading=19, spaceBefore=12, spaceAfter=7, keepWithNext=True, textColor=HexColor(ACCENT), wordWrap='CJK'),
    'p': ParagraphStyle('p', fontName='KR', fontSize=9.2, leading=15, spaceAfter=6, wordWrap='CJK'),
    'li': ParagraphStyle('li', fontName='KR', fontSize=9.2, leading=15, spaceAfter=3, leftIndent=12, bulletIndent=2, wordWrap='CJK'),
    'cell': ParagraphStyle('cell', fontName='KR', fontSize=8, leading=12.4, wordWrap='CJK'),
    'cellb': ParagraphStyle('cellb', fontName='KRB', fontSize=8, leading=12.4, wordWrap='CJK'),
    'code': ParagraphStyle('code', fontName='KR', fontSize=7.9, leading=12, spaceAfter=10, backColor=HexColor(SOFT), borderPadding=8, wordWrap='CJK'),
    'meta': ParagraphStyle('meta', fontName='KR', fontSize=8, leading=13, spaceAfter=6, textColor=HexColor(MUTED)),
    'note': ParagraphStyle('note', fontName='KR', fontSize=8.6, leading=14, spaceAfter=8, backColor=HexColor('#fff6e0'), borderPadding=7, wordWrap='CJK'),
}
story = []


def P(text, style='p'):
    return Paragraph(html.escape(str(text)).replace('\n', '<br/>'), S[style])


def title(text):
    story.extend([P(STAMP, 'meta'), P(text, 'title')])


def h(text):
    story.append(P(text, 'h'))


def p(text):
    story.append(P(text))


def bullets(items):
    for item in items:
        story.append(Paragraph(html.escape(item), S['li'], bulletText='•'))
    story.append(Spacer(1, 4))


def code(text):
    story.append(P(text, 'code'))


def note(text):
    story.extend([P(text, 'note'), Spacer(1, 10)])


def table(headers, rows, widths):
    data = [[P(v, 'cellb') for v in headers]] + [[P(v, 'cell') for v in row] for row in rows]
    t = Table(data, colWidths=widths, repeatRows=1, hAlign='LEFT')
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#e0ece5')), ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6), ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 5), ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LINEBELOW', (0, 0), (-1, -1), .4, HexColor(LINE))]))
    story.extend([t, Spacer(1, 8)])


def page(text):
    story.append(PageBreak())
    title(text)


def footer(c, doc):
    c.setStrokeColor(HexColor('#d8e3dc'))
    c.line(46, 42, 549, 42)
    c.setFont('KR', 7.5)
    c.setFillColor(HexColor(MUTED))
    c.drawString(46, 28, 'NODEVERSE / 팀 공유용 / 서버 파트 변경사항·진행상황')
    c.drawRightString(549, 28, str(doc.page))


# 1. Summary ---------------------------------------------------------------
title('서버 파트 변경사항 · 진행상황')
p('게임 팀이 올린 회원·클라우드 세이브 API(커밋 5b79ea4)를 기준으로, 서버 파트 기능(로그인 기록, 관리자 대시보드, 업데이트 배포)을 붙였습니다. '
  '게임이 쓰는 API의 요청·응답 형식은 바꾸지 않았으므로 게임 클라이언트는 수정할 것이 없습니다.')
table(['항목', '내용'], [
    ['GitHub', '저장소 MLO_3rd_project_dashboard / 브랜치 server/live-members-releases / 커밋 5824299\n아직 main에 합치지 않았습니다. 검토 후 Pull Request로 합칩니다.'],
    ['서버 PC MySQL (192.168.0.167)', '마이그레이션 적용 완료. game_accounts 테이블 생성, 쓰지 않는 game_member_credentials 삭제'],
    ['서버 PC MongoDB (192.168.0.167)', 'Django에서 접속 확인, 인덱스 생성 완료. rt_* 실시간 컬렉션은 아직 비어 있음(파이프라인 연결 전)'],
    ['Django (192.168.0.29:8000)', '실행 중. API 5개, 로그인 기록, 게임 회원 화면을 실제 서버 DB로 확인함'],
    ['테스트', '자동 테스트 51개 통과'],
], [140, 363])

h('데이터가 가는 길')
code('게임 → Django /api/game/auth/*  → MySQL(서버 PC)    회원가입 · 로그인 · 클라우드 세이브 · 로그인 기록\n'
     '게임 → 수집 API /v2/events → Kafka → Spark → MongoDB(서버 PC) rt_* → Django 실시간 현황\n'
     '게임 → Django /api/game/manifest, /downloads/*     업데이트 확인 · 리소스 팩 · EXE 다운로드')
table(['저장소', '저장하는 것'], [
    ['MySQL nodeverse', '회원 계정(game_accounts, game_members), 로그인 기록(game_login_history), 릴리스·리소스 팩(game_releases, game_content_packs), 관리자 계정(admin_accounts)'],
    ['MongoDB nodeverse_logs', '게임 플레이 로그, 파이프라인 실시간 집계(rt_minigame_1m, rt_alerts, rt_summary, rt_updates, rt_versions)'],
], [140, 363])

# 2. Changes -----------------------------------------------------------------
page('01. 변경한 내용')
h('게임 회원 API (/api/game/auth/*) - 형식은 그대로, 서버 쪽 동작만 추가')
table(['API', '보내는 값', '추가된 동작'], [
    ['register', 'username, password, recovery_key(선택)', '가입 성공·실패가 기록됨'],
    ['login', 'username, password', '성공·실패와 사유(아이디 없음, 비밀번호 틀림)가 기록됨'],
    ['find-id', 'recovery_key', '조회 결과가 기록됨'],
    ['reset-password', 'username, recovery_key, new_password', '복구 키가 등록되어 있고 맞을 때만 변경(보안 수정)'],
    ['save', 'username, save_data', '변경 없음'],
], [80, 175, 248])
bullets([
    '기록에는 성공 여부, 실패 사유, IP가 남습니다. 게임이 install_id, build_version, content_version을 같이 보내면 그 값도 남습니다(보내지 않아도 동작은 같음).',
    '요청 제한: IP당 1분에 30회, 아이디당 10분에 로그인·재설정 실패 10회를 넘으면 429와 {"success": false, "message": ...}를 돌려줍니다. 게임은 message를 그대로 보여 주면 됩니다.',
    '비밀번호 재설정: 예전에는 복구 키 없이 가입한 계정을 누구나 재설정할 수 있었습니다. 이제 그런 계정은 403입니다.',
])

h('관리자 대시보드 (관리자 로그인 필요)')
table(['화면', '내용'], [
    ['/staff/members/', '게임 회원 목록: 가입일, 마지막 로그인, 로그인·실패 횟수, 클라우드 세이브 기준 미니게임 클리어·별·점수, 일별 로그인 그래프, 최근 가입·로그인 기록'],
    ['/staff/members/<회원 ID>/', '회원 상세: 영역별(자료구조·알고리즘·SQL·데이터) 24개 미니게임 클리어 현황, 가입·로그인 기록 전체'],
    ['/staff/live/', '실시간 학습 현황: 최근 1분 이벤트, 5분 활성 세션, 미니게임별 성공률 추이, 실패 급증 경고. 3초마다 갱신, 30초 넘게 새 값이 없으면 "수집 지연" 표시'],
    ['/staff/live/?tab=updates', '업데이트 진행: 버전별 보급률, 최소 빌드 미만 설치, 팩 다운로드 추이·실패 사유. 실패율이 높으면 "팩 비활성화 검토" 표시'],
    ['/staff/releases/', 'EXE 릴리스와 리소스 팩 등록, 켜기/끄기. 팩의 SHA-256은 서버가 직접 계산. 팩을 끄면 다음 실행부터 이전 팩이 나감'],
    ['/staff/download/', '관리자용 게임 다운로드 탭'],
], [130, 373])

h('공개 주소 (로그인 없음)')
table(['주소', '내용'], [
    ['/  (홈페이지)', '"게임 다운로드" 메뉴와 다운로드 섹션 추가'],
    ['/download/', '최신 EXE 다운로드 페이지와 설치 방법(SmartScreen 안내 포함)'],
    ['GET /api/game/manifest?channel=windows-stable', '게임이 시작할 때 읽는 업데이트 정보. 60초 캐시, ETag. 릴리스가 없으면 404(게임은 오프라인으로 처리)'],
    ['/downloads/packs/<파일>', '리소스 팩 파일'],
], [185, 318])

h('그 밖의 변경')
bullets([
    '관리자 API: GET /api/admin/live/{summary, minigames, alerts, updates}?minutes=1~180 (관리자 전용, 캐시 안 함)',
    '미니게임 영역은 보낸 category가 아니라 minigame_id로 정합니다(ST06, ST09는 알고리즘 영역).',
    '관리자 로그인 버튼을 두 번 누르면 "CSRF 검증 실패"가 뜨던 문제를 고쳤습니다.',
    'manage.py seed_rt: 파이프라인 연결 전 화면 확인용 목업 데이터. seed_rt --clear는 목업만 지웁니다.',
    '연동 안내 문서: docs/server-integration.md',
])

# 3. Verification -------------------------------------------------------------
page('02. 확인 결과')
p('실행 중인 서버(192.168.0.29:8000)에 시험 계정으로 직접 요청해서 서버 PC MySQL에 저장되는 것을 확인했습니다. 확인 후 시험 계정은 지웠습니다.')
table(['확인 항목', '결과'], [
    ['회원가입 / 같은 아이디로 다시 가입', '201 / 409'],
    ['로그인: 틀린 비밀번호 / 맞는 비밀번호', '401 / 200'],
    ['저장 후 다시 로그인', '저장한 클리어 기록이 그대로 돌아옴'],
    ['아이디 찾기', '200'],
    ['비밀번호 재설정: 틀린 복구 키 / 맞는 복구 키', '403 / 200'],
    ['로그인 기록', '시도 8건이 성공·실패 사유·IP와 함께 game_login_history에 저장됨'],
    ['게임 회원 화면', '정상 표시(로그인·실패 수, 클리어 2, 별 4, 점수 30)'],
    ['MongoDB 연결', '서버 PC 27017 접속, 인덱스 생성 완료'],
], [220, 283])

h('현재 공유 DB 상태')
bullets([
    'game_accounts: 0명 (실제 게임 회원 없음)',
    'game_login_history: 예전 시험 계정(server_test01) 기록 3건이 남아 있음',
    '관리자 계정: 생성됨(/staff/register/ 초대 코드 방식)',
])

# 4. To-dos per team -----------------------------------------------------------
page('03. 팀별로 해 주실 일')
h('서버 PC 담당 (192.168.0.167)')
bullets([
    'MongoDB 인증 켜기: 지금은 계정 없이 접속됩니다. 계정을 만든 뒤 security.authorization: enabled를 적용해 주세요. 계정 예시는 output/server_setup/02_mongodb_accounts.js에 있습니다.',
    '필요한 계정: 파이프라인 Spark용(nodeverse_logs의 rt_* 쓰기), Django용(읽기 전용)',
    '방화벽: 27017은 Django PC(.29)와 파이프라인 PC만, 3306은 Django PC만 허용',
])
h('파이프라인 담당')
bullets([
    'Spark의 MongoDB 출력 주소를 서버 PC(192.168.0.167:27017, DB nodeverse_logs)로 바꿔 주세요. 지금은 Docker 안의 127.0.0.1에 씁니다.',
    '컬렉션 이름과 _id 규칙(rt_minigame_1m, rt_alerts, rt_summary, rt_updates, rt_versions)은 공통 계약 그대로입니다.',
    'window_start, updated_at은 BSON Date(UTC)로 넣어 주세요. Django가 이 필드로 시간 범위를 조회합니다.',
    '수집 API를 다른 PC에서 받을 수 있게 COLLECTOR_BIND=0.0.0.0으로 열어 주세요.',
    '예전에 요청했던 learning_events 컬렉션은 필요 없어졌습니다. 진행률은 클라우드 세이브에서 읽습니다.',
])
h('게임 담당')
bullets([
    '서버 주소를 http://192.168.0.29:8000 으로 맞춰 주세요(회원 API, 매니페스트).',
    '진행률 표시: save_data.minigame_cleared의 키를 24개 실행 ID(ST01~ST10, DS09, DS10, ALG01~ALG04, SQL01~SQL04, DATA01~DATA04)로 저장하면 영역별 카드에 표시됩니다. 값은 별 개수(0~3) 또는 true. 다른 이름의 키는 "다른 이름으로 저장된 클리어 기록"에 따로 나옵니다.',
    '선택: 회원 API 요청에 install_id, build_version, content_version을 같이 보내면 어떤 설치·버전에서 로그인했는지 대시보드에 나옵니다.',
    '429 응답(요청 제한)이 오면 message를 그대로 보여 주세요.',
    '리소스 팩(.pck)을 만들면 서버 담당에게 파일과 필요한 최소 빌드를 전달해 주세요.',
])
h('서버 담당 (남은 일)')
bullets([
    '브랜치 server/live-members-releases를 Pull Request로 main에 합치기',
    'Django PC 네트워크를 "개인"으로 바꾸기: 지금 "공용"이라 8000 포트 방화벽 규칙(개인·도메인)이 적용되지 않아 다른 PC에서 접속이 막힐 수 있음',
    '첫 EXE 릴리스와 리소스 팩을 /staff/releases/에 등록',
    'MongoDB 인증이 켜지면 .env의 MONGODB_URI를 읽기 전용 계정 주소로 변경',
])

# 5. Open issues ---------------------------------------------------------------
page('04. 같이 정해야 할 보안 과제')
table(['문제', '영향', '제안'], [
    ['/save에 인증이 없음', '아이디만 알면 누구나 그 계정의 세이브를 덮어쓸 수 있음', '로그인 때 서버가 토큰을 발급하고, /save에서 토큰을 확인. 게임도 토큰을 보내도록 수정 필요'],
    ['비밀번호 최소 3자', '쉽게 추측 가능', '외부 공개 전에 8자 이상으로 상향'],
    ['오류 메시지로 아이디 존재 여부가 드러남', '가입된 아이디를 알아낼 수 있음', '"아이디 또는 비밀번호가 틀렸습니다"로 통일(게임 UI 문구도 함께 변경)'],
    ['MongoDB 인증 꺼짐', '같은 네트워크에서 누구나 로그 DB에 접근', '서버 PC 담당 1번 항목'],
    ['관리자 초대 코드가 공용', '코드가 새면 누구나 관리자 가입 가능', '외부 공개 전에 일회용 초대로 교체'],
], [125, 170, 208])
note('게임과 홈페이지에는 DB 비밀번호, GAME_SERVER_API_KEY, 관리자 초대 코드를 넣지 않습니다. .env 파일은 깃에 올리지 않습니다.')

h('내 PC에서 실행해 보기')
code('git fetch origin\n'
     'git switch server/live-members-releases\n'
     '.venv/Scripts/python.exe -m pip install -r requirements.txt\n'
     '.venv/Scripts/python.exe manage.py migrate      # 공유 DB에는 이미 적용됨\n'
     '.venv/Scripts/python.exe manage.py runserver 0.0.0.0:8000')
p('관리자 계정은 manage.py createsuperuser로 만들거나, 서버 담당에게 초대 코드를 받아 /staff/register/에서 가입합니다. .env를 바꾸면 서버를 다시 켜야 적용됩니다.')

OUT.mkdir(parents=True, exist_ok=True)
doc = SimpleDocTemplate(str(OUT / FILENAME), pagesize=(595.28, 841.89), leftMargin=46, rightMargin=46,
                        topMargin=42, bottomMargin=57, title='NODEVERSE 서버 파트 변경사항·진행상황', author='NODEVERSE')
doc.build(story, onFirstPage=footer, onLaterPages=footer)
print(OUT / FILENAME)
