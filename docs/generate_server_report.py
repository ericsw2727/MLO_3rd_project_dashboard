"""Server part result report (구현결과서) with the game team's to-do list.
Run: .venv/Scripts/python.exe docs/generate_server_report.py
"""
from pathlib import Path
import html

from reportlab.lib.colors import HexColor
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output/pdf'
FILENAME = 'NODEVERSE_서버파트_구현결과서.pdf'
STAMP = 'NODEVERSE / 서버 파트 구현결과서 / 2026.11.20 / v1.0'

pdfmetrics.registerFont(TTFont('KR', 'C:/Windows/Fonts/malgun.ttf'))
pdfmetrics.registerFont(TTFont('KRB', 'C:/Windows/Fonts/malgunbd.ttf'))
INK, ACCENT, MUTED, LINE, SOFT = '#173d35', '#176b57', '#6f8177', '#dce5e0', '#edf3f0'
S = {
    'cover': ParagraphStyle('cover', fontName='KRB', fontSize=26, leading=36, spaceAfter=8, textColor=HexColor(INK), wordWrap='CJK'),
    'title': ParagraphStyle('title', fontName='KRB', fontSize=19, leading=28, spaceAfter=10, textColor=HexColor(INK), wordWrap='CJK'),
    'h': ParagraphStyle('h', fontName='KRB', fontSize=12.5, leading=19, spaceBefore=11, spaceAfter=6, keepWithNext=True, textColor=HexColor(ACCENT), wordWrap='CJK'),
    'h3': ParagraphStyle('h3', fontName='KRB', fontSize=10.2, leading=16, spaceBefore=7, spaceAfter=4, keepWithNext=True, textColor=HexColor(INK), wordWrap='CJK'),
    'p': ParagraphStyle('p', fontName='KR', fontSize=9.2, leading=15, spaceAfter=6, wordWrap='CJK'),
    'li': ParagraphStyle('li', fontName='KR', fontSize=9.1, leading=14.6, spaceAfter=3, leftIndent=12, bulletIndent=2, wordWrap='CJK'),
    'cell': ParagraphStyle('cell', fontName='KR', fontSize=8, leading=12.3, wordWrap='CJK'),
    'cellb': ParagraphStyle('cellb', fontName='KRB', fontSize=8, leading=12.3, wordWrap='CJK'),
    'code': ParagraphStyle('code', fontName='KR', fontSize=7.8, leading=11.6, spaceAfter=9, backColor=HexColor(SOFT), borderPadding=8, wordWrap='CJK'),
    'meta': ParagraphStyle('meta', fontName='KR', fontSize=8, leading=13, spaceAfter=6, textColor=HexColor(MUTED)),
    'warn': ParagraphStyle('warn', fontName='KR', fontSize=9, leading=14.6, spaceAfter=6, backColor=HexColor('#fdecea'), borderPadding=8, wordWrap='CJK'),
    'note': ParagraphStyle('note', fontName='KR', fontSize=8.6, leading=14, spaceAfter=6, backColor=HexColor('#fff6e0'), borderPadding=7, wordWrap='CJK'),
}
story = []


def P(text, style='p'):
    return Paragraph(html.escape(str(text)).replace('\n', '<br/>'), S[style])


def title(text):
    story.extend([P(STAMP, 'meta'), P(text, 'title')])


def h(text):
    story.append(P(text, 'h'))


def h3(text):
    story.append(P(text, 'h3'))


def p(text):
    story.append(P(text))


def bullets(items):
    for item in items:
        story.append(Paragraph(html.escape(item), S['li'], bulletText='•'))
    story.append(Spacer(1, 4))


def code(text):
    # Keep indentation (GDScript needs it): spaces become non-breaking spaces.
    body = html.escape(text).replace(' ', '&nbsp;').replace('\n', '<br/>')
    story.append(Paragraph(body, S['code']))


def boxed(text, style):
    story.extend([P(text, style), Spacer(1, 8)])


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
    c.drawString(46, 28, 'NODEVERSE / 서버 파트 구현결과서 / 팀 공유용')
    c.drawRightString(549, 28, str(doc.page))


# ---------------------------------------------------------------------------
# Cover & summary
story.append(P(STAMP, 'meta'))
story.append(P('서버 파트 구현결과서', 'cover'))
p('대상: 게임·파이프라인·서버 PC 담당자 / 저장소: MLO_3rd_project_dashboard (main, 커밋 3cd3925)')
h('1. 요약')
p('서버 파트는 게임 회원 정보와 로그인 기록을 서버 PC의 MySQL에 모으고, 관리자 대시보드에서 회원·진행률·실시간 현황·업데이트 배포를 관리하도록 구현했습니다. '
  '게임 팀이 만든 회원·클라우드 세이브 API(5b79ea4)를 기준으로 삼아 형식은 그대로 두고, 기록·요청 제한·보안 수정을 서버 쪽에 더했습니다.')
table(['구분', '상태'], [
    ['서버 기능 (API, 대시보드, 업데이트 배포)', '완료. 자동 테스트 51개 통과, 실제 서버 DB로 API 5개 확인'],
    ['서버 PC MySQL (192.168.0.167)', '마이그레이션 적용 완료. 회원 테이블 game_accounts 생성'],
    ['서버 PC MongoDB (192.168.0.167)', '접속·인덱스 확인. 실시간 집계(rt_*)는 파이프라인 연결 대기'],
    ['게임 → 서버 로그인 연동', '미연결. 게임의 요청이 Django가 아닌 파이프라인 PC로 가고 있음 (4장)'],
    ['파이프라인 → 서버 MongoDB', '미연결. Spark 출력 주소 변경 필요 (6장)'],
], [190, 313])
boxed('가장 먼저 해결할 것: 지금 게임에서 회원가입·로그인을 해도 서버에 기록되지 않습니다. 게임이 회원 API를 이벤트 수집 서버 주소(192.168.0.81:8000)로 보내고 있어서, '
      '404를 받고 "서버 꺼짐"으로 판단해 이 PC의 로컬 계정으로만 처리합니다. 게임 파트 할 일 1~3번(5장)을 반영하면 해결됩니다.', 'warn')

h('2. 시스템 구성')
table(['역할', '위치', '맡는 일'], [
    ['Django 서버', '192.168.0.29:8000', '게임 회원 API, 관리자 대시보드, 업데이트 매니페스트·다운로드'],
    ['MySQL nodeverse', '192.168.0.167:3306', '회원 계정, 로그인 기록, 릴리스·리소스 팩, 관리자 계정'],
    ['MongoDB nodeverse_logs', '192.168.0.167:27017', '게임 플레이 로그, 파이프라인 실시간 집계 rt_*'],
    ['수집 API · Kafka · Spark', '192.168.0.81:8000 (파이프라인 PC)', '게임 학습 이벤트 수집·집계'],
], [118, 160, 225])
code('[회원]   게임 ── /api/game/auth/* ──▶ Django(.29) ──▶ MySQL(.167)   가입·로그인·찾기·저장 + 로그인 기록\n'
     '[로그]   게임 ── /v2/events ──▶ 수집 API(.81) ─▶ Kafka ─▶ Spark ─▶ MongoDB(.167) rt_* ──▶ Django 실시간 현황\n'
     '[배포]   게임 ── /api/game/manifest, /downloads/* ──▶ Django(.29)       업데이트 확인·리소스 팩·EXE')
p('핵심: 게임은 서로 다른 두 서버에 요청합니다. 이벤트는 파이프라인 PC(.81), 회원·저장·업데이트는 Django(.29)입니다.')

# ---------------------------------------------------------------------------
page('3. 구현 내용')
h('3-1. 게임 회원 API (/api/game/auth/*)')
p('요청·응답 형식은 게임 팀 구현(5b79ea4) 그대로입니다. 모든 요청은 POST, Content-Type: application/json이고 응답은 {"success": true/false, "message": ...} 형식입니다.')
table(['API', '보내는 값', '성공 응답', '서버에서 추가한 동작'], [
    ['register', 'username, password, recovery_key(선택)', '201 username, player_id, save_data', '시도 기록'],
    ['login', 'username, password', '200 username, player_id, save_data', '성공·실패 사유 기록, 실패 누적 시 잠금'],
    ['find-id', 'recovery_key', '200 usernames', '시도 기록'],
    ['reset-password', 'username, recovery_key, new_password', '200', '복구 키가 등록·일치할 때만 변경'],
    ['save', 'username, save_data', '200', '없음 (last_saved 시각 추가)'],
], [68, 140, 140, 155])
bullets([
    '로그인 기록(game_login_history): 종류, 성공 여부, 실패 사유, IP, 시각. 요청에 install_id, build_version, content_version이 있으면 같이 저장합니다.',
    '요청 제한: IP당 1분 30회, 아이디당 10분 동안 로그인·재설정 실패 10회. 넘으면 429와 message를 돌려줍니다.',
    '보안 수정: 복구 키 없이 가입한 계정은 누구나 비밀번호를 바꿀 수 있던 문제를 막았습니다(403).',
])
h('3-2. 관리자 대시보드')
table(['화면', '내용'], [
    ['/staff/members/', '게임 회원 목록: 가입일, 마지막 로그인, 로그인·실패 수, 미니게임 클리어·별·점수, 일별 로그인, 최근 기록'],
    ['/staff/members/<회원 ID>/', '회원 상세: 영역별 24개 미니게임 클리어 현황, 가입·로그인 기록 전체'],
    ['/staff/live/', '실시간 학습 현황(3초 갱신): 최근 1분 이벤트, 활성 세션, 미니게임별 성공률, 실패 급증 경고'],
    ['/staff/live/?tab=updates', '업데이트 진행: 버전별 보급률, 팩 다운로드 추이·실패 사유'],
    ['/staff/releases/', 'EXE 릴리스·리소스 팩 등록과 켜기/끄기(팩 SHA-256은 서버가 계산)'],
    ['/staff/download/', '관리자용 게임 다운로드 탭'],
], [130, 373])
h('3-3. 공개 주소와 DB')
table(['주소 / 테이블', '내용'], [
    ['/ , /download/', '홈페이지 게임 다운로드 섹션, 다운로드·설치 안내 페이지'],
    ['GET /api/game/manifest', '게임 업데이트 정보. 60초 캐시, ETag. 릴리스가 없으면 404'],
    ['game_accounts', '게임 회원 계정(아이디, 비밀번호 해시, 복구 키, 클라우드 세이브 JSON)'],
    ['game_members', '회원 기본 정보(대시보드 플레이어). game_accounts와 1:1'],
    ['game_login_history', '가입·로그인·아이디 찾기·비밀번호 재설정 시도 기록'],
    ['game_releases, game_content_packs', 'EXE 릴리스와 리소스 팩'],
], [160, 343])

# ---------------------------------------------------------------------------
page('4. 검증 결과와 게임 연동 점검')
h('4-1. 서버 검증')
table(['항목', '결과'], [
    ['자동 테스트', '51개 통과 (회원 API, 기록, 요청 제한, 매니페스트, 실시간 API, 관리자 로그인)'],
    ['실제 서버 회원가입 / 중복 가입', '201 / 409'],
    ['로그인: 틀린 비밀번호 / 맞는 비밀번호', '401 / 200'],
    ['저장 후 다시 로그인', '클리어 기록 그대로 복원'],
    ['아이디 찾기, 재설정(틀린 키 / 맞는 키)', '200, 403 / 200'],
    ['로그인 기록 저장', '시도 8건 모두 MySQL game_login_history에 저장'],
    ['게임 회원 화면', '회원·로그인 수·클리어·별·점수 정상 표시'],
], [200, 303])
p('시험 계정은 확인 후 삭제했습니다. 현재 game_accounts는 0명입니다.')

h('4-2. 게임 클라이언트 점검 (nodeverse-game 최신 코드 기준)')
p('게임 저장소의 scripts/network_manager.gd, scripts/nodeverse_world.gd, scripts/minigames/*를 읽고, 실제로 요청을 보내 확인했습니다.')
table(['점검 항목', '결과', '근거'], [
    ['회원 API를 보내는 주소', '문제', 'game_auth_request()와 sync_cloud_save()가 이벤트용 주소 get_base_url()을 씀. 기본값 192.168.0.81:8000(파이프라인 PC). 이 주소의 /api/game/auth/login은 404'],
    ['404 처리', '문제', 'code == 404를 "오프라인"으로 처리해 로컬 계정으로 대체. Django도 아이디 찾기 결과 없음·없는 아이디 재설정에 404를 돌려주므로 서버가 켜져 있어도 오프라인으로 오인'],
    ['/api/game/player-login 호출', '문제', '로그인 후 sync_player_login()이 서버 간 전용 API를 이벤트 주소와 기본 토큰으로 호출(서버 키가 없어 성공할 수 없음). 게임에는 서버 키를 넣으면 안 되며, 이미 가입·로그인 응답에 player_id가 있음'],
    ['오프라인 대체', '주의', '서버에 못 붙으면 로컬에서 가입·로그인 성공 처리. 이 계정은 서버에 없고 기록도 남지 않음'],
    ['미니게임 저장 키', '정상', 'stage_id(ST01~ST10, DS09, DS10, ALG01~04, SQL01~04, DATA01~04)가 서버 카탈로그와 같음'],
    ['자동 저장 시점', '정상', '창 닫기, 미니게임 복귀 시 /save 호출'],
    ['이벤트 player_id', '확인 필요', '로그인 후 이벤트 player_id를 서버 회원 ID로 바꿈. 공통 계약은 설치 ID. 팀 합의 필요'],
], [118, 52, 333])

# ---------------------------------------------------------------------------
page('5. 게임 파트 할 일')
p('목표: 게임에서 회원가입·로그인·아이디 찾기·비밀번호 재설정·저장을 하면 그 정보가 Django(192.168.0.29:8000)를 거쳐 서버 PC MySQL에 저장되고, 관리자 대시보드에 바로 보이는 것. '
  '1~3번은 이 목표를 위해 꼭 필요하고, 4~6번은 권장입니다.')

h3('[필수 1] 회원 API 주소를 이벤트 주소와 분리')
p('network_manager.gd에 Django용 주소를 따로 두고, 회원 API와 저장에서 그 주소를 쓰게 바꿉니다. 이벤트(/v2/events)는 지금처럼 파이프라인 PC로 보냅니다.')
code('const DEFAULT_API_HOST: String = "192.168.0.29"   # Django 서버\n'
     'const DEFAULT_API_PORT: int = 8000\n'
     'var api_host: String = DEFAULT_API_HOST\n'
     'var api_port: int = DEFAULT_API_PORT\n\n'
     'func get_api_base_url() -> String:\n'
     '    return "http://%s:%d" % [api_host, api_port]\n\n'
     '# load_config():  api_host = str(d.get("api_host", DEFAULT_API_HOST)).strip_edges()\n'
     '#                 api_port = int(d.get("api_port", DEFAULT_API_PORT))\n'
     '# save_config():  "api_host": api_host, "api_port": api_port 추가\n'
     '# game_auth_request(), sync_cloud_save():  get_base_url() → get_api_base_url()')
p('이미 설치된 PC에는 user://network_config.json이 남아 있으므로, api_host가 없을 때 기본값이 쓰이는지 확인해 주세요. 디버그 패널에서 api_host를 바꿀 수 있으면 시험이 편합니다.')

h3('[필수 2] 서버 응답을 "오프라인"으로 오인하지 않기')
p('HTTP 상태 코드가 아니라 응답 본문으로 판단합니다. JSON에 success 키가 있으면 서버가 답한 것이므로 online으로 처리하고, 그 message를 보여 줍니다.')
code('var parsed = JSON.parse_string(body.get_string_from_utf8())\n'
     'var is_server_reply: bool = parsed is Dictionary and parsed.has("success")\n'
     'if result != HTTPRequest.RESULT_SUCCESS or code == 0 or code >= 500 or not is_server_reply:\n'
     '    return {"online": false, "code": code, "data": {}}\n'
     'return {"online": true, "code": code, "data": parsed}')

h3('[필수 3] sync_player_login() 호출 제거')
p('nodeverse_world.gd의 _on_login_success()에서 sync_player_login 호출을 지웁니다. /api/game/player-login은 서버 간 전용(GAME_SERVER_API_KEY 필요)이라 게임에서 부르면 안 됩니다. '
  '서버 회원 ID는 register·login 응답의 player_id를 쓰면 됩니다(이미 AuthManager.set_server_player_id로 저장 중).')

h3('[권장 4] 회원 API 요청에 설치·버전 정보 추가')
p('game_auth_request()에서 아래 세 값을 payload에 넣으면, 대시보드 로그인 기록에 어느 설치·버전에서 로그인했는지 나옵니다. 서버는 없어도 동작합니다.')
code('payload["install_id"] = _get_or_create_install_id()\n'
     'payload["build_version"] = get_build_version()\n'
     'payload["content_version"] = content_version')

h3('[권장 5] 오프라인일 때 사용자에게 알리기')
bullets([
    '서버에 연결되지 않아 로컬로 처리될 때 "오프라인 모드: 이 PC에만 저장됩니다"를 화면에 표시해 주세요.',
    '회원가입은 서버 연결이 필요하도록 막는 것을 권장합니다. 오프라인에서 만든 계정은 서버에 없어서 다른 PC에서 로그인할 수 없고 대시보드에도 안 나옵니다.',
    '429(요청 제한)와 403(복구 키 불일치) 응답의 message는 그대로 보여 주면 됩니다.',
])

h3('[권장 6] 업데이트 매니페스트 주소')
p('매니페스트도 Django 주소입니다: http://192.168.0.29:8000/api/game/manifest?channel=windows-stable. 릴리스가 없으면 404이며, 이때는 지금처럼 업데이트 없이 실행하면 됩니다.')

# ---------------------------------------------------------------------------
h('5-1. 게임 연동 확인 절차')
p('게임 파트 1~3번을 반영한 뒤 아래 순서로 확인합니다. 서버 담당이 대시보드를 같이 띄워 두면 바로 확인할 수 있습니다.')
table(['순서', '게임에서 할 일', '서버에서 보이는 것 (/staff/members/)'], [
    ['0', '게임 PC 브라우저에서 http://192.168.0.29:8000/ 접속', '홈페이지가 열리면 네트워크 정상'],
    ['1', '새 아이디로 회원가입(복구 키 입력)', '회원 목록에 새 아이디, 최근 기록에 "회원가입 · 성공"'],
    ['2', '틀린 비밀번호로 로그인', '최근 기록에 "로그인 · wrong_password"'],
    ['3', '맞는 비밀번호로 로그인', '마지막 로그인 시각 갱신, 로그인 수 +1'],
    ['4', '미니게임 1개 클리어 후 복귀', '미니게임 클리어·별 증가, 마지막 저장 시각 갱신'],
    ['5', '게임 종료 후 다른 PC에서 같은 아이디로 로그인', '이어하기로 위치·점수·별이 복원됨'],
    ['6', '아이디 찾기, 비밀번호 재설정', '최근 기록에 "아이디 찾기", "비밀번호 재설정"'],
], [32, 210, 261])
boxed('0번이 안 되면 게임 문제가 아니라 네트워크 문제입니다. Django PC(.29)의 네트워크 프로필이 "공용"이면 8000 포트가 막히므로 "개인"으로 바꿔야 합니다(서버 담당).', 'note')

h('6. 다른 파트 할 일')
h3('파이프라인 담당')
bullets([
    'Spark의 MongoDB 출력 주소를 서버 PC(192.168.0.167:27017, nodeverse_logs)로 변경. 컬렉션·_id 규칙(rt_*)은 공통 계약 그대로.',
    'window_start, updated_at은 BSON Date(UTC). 수집 API는 COLLECTOR_BIND=0.0.0.0으로 외부 PC 수신 허용.',
    '예전에 요청한 learning_events 컬렉션은 필요 없음(진행률은 클라우드 세이브에서 읽음).',
])
h3('서버 PC 담당 (192.168.0.167)')
bullets([
    'MongoDB 인증 켜기(현재 계정 없이 접속됨). Spark용 쓰기 계정, Django용 읽기 전용 계정 생성.',
    '방화벽: 27017은 Django PC·파이프라인 PC만, 3306은 Django PC만 허용.',
])
h3('서버 담당 (남은 일)')
bullets([
    'Django PC 네트워크 프로필을 "개인"으로 변경(다른 PC 접속 허용).',
    '첫 EXE 릴리스·리소스 팩 등록, MongoDB 인증 후 MONGODB_URI를 읽기 전용 계정으로 변경.',
])

# ---------------------------------------------------------------------------
page('7. 남은 과제')
table(['과제', '내용', '담당'], [
    ['/save 인증', '아이디만 알면 남의 세이브를 덮어쓸 수 있음. 로그인 때 토큰 발급 → /save에서 확인', '서버 + 게임'],
    ['비밀번호 최소 길이', '현재 3자. 외부 공개 전 8자 이상', '서버 + 게임(UI 안내)'],
    ['오류 문구 통일', '"존재하지 않는 아이디"로 가입 여부가 드러남. "아이디 또는 비밀번호가 틀렸습니다"로 통일', '서버 + 게임'],
    ['이벤트 player_id 기준', '계약은 설치 ID, 게임은 로그인 후 회원 ID 사용. 하나로 합의', '게임 + 파이프라인'],
    ['MongoDB 인증', '같은 네트워크에서 누구나 로그 DB 접근 가능', '서버 PC'],
    ['관리자 초대 코드', '공용 코드 방식. 외부 공개 전 일회용 초대로 교체', '서버'],
], [100, 293, 110])
boxed('게임과 홈페이지에는 DB 비밀번호, GAME_SERVER_API_KEY, 관리자 초대 코드를 넣지 않습니다. .env는 깃에 올리지 않습니다.', 'note')
h('부록. 서버 실행')
code('git pull origin main\n'
     '.venv/Scripts/python.exe -m pip install -r requirements.txt\n'
     '.venv/Scripts/python.exe manage.py migrate        # 공유 DB에는 이미 적용됨\n'
     '.venv/Scripts/python.exe manage.py runserver 0.0.0.0:8000')
p('관리자 계정: manage.py createsuperuser 또는 초대 코드로 /staff/register/ 가입. .env를 바꾸면 서버를 다시 켜야 적용됩니다. '
  '자세한 연동 규격은 저장소의 docs/server-integration.md를 봅니다.')

OUT.mkdir(parents=True, exist_ok=True)
doc = SimpleDocTemplate(str(OUT / FILENAME), pagesize=(595.28, 841.89), leftMargin=46, rightMargin=46,
                        topMargin=42, bottomMargin=57, title='NODEVERSE 서버 파트 구현결과서', author='NODEVERSE')
doc.build(story, onFirstPage=footer, onLaterPages=footer)
print(OUT / FILENAME)
