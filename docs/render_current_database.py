"""Render the verified current database structure as a single shareable PNG."""
from pathlib import Path
import math
import json
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
snapshot = json.loads((ROOT / 'docs' / 'database_structure.json').read_text(encoding='utf-8'))
assert {entry['name'] for entry in snapshot['mysql']} == {
    'admin_accounts', 'game_members', 'admin_group_memberships', 'admin_permission_assignments',
    'auth_group', 'auth_group_permissions', 'auth_permission', 'django_session',
    'django_content_type', 'django_migrations',
}
assert {entry['name'] for entry in snapshot['mongodb']} == {
    'game_sessions', 'game_problems', 'problem_runs', 'solution_attempts', 'gameplay_events',
}
WIDTH, HEIGHT = 3400, 2340
BACKGROUND = '#f3f6fa'
INK, MUTED = '#14283f', '#62748a'
BLUE, GREEN = '#2167b7', '#178064'
image = Image.new('RGB', (WIDTH, HEIGHT), BACKGROUND)
draw = ImageDraw.Draw(image)


def font(size, bold=False, mono=False):
    name = 'consolab.ttf' if mono else 'malgunbd.ttf' if bold else 'malgun.ttf'
    return ImageFont.truetype('C:/Windows/Fonts/' + name, size)


def text(x, y, value, size=28, color=INK, bold=False, mono=False):
    draw.text((x, y), value, font=font(size, bold, mono), fill=color)


def pill(x, y, label, color, fill):
    width = draw.textlength(label, font=font(24, True)) + 36
    draw.rounded_rectangle((x, y, x + width, y + 48), radius=24, fill=fill)
    text(x + 18, y + 6, label, 24, color, True)


def panel(x, y, width, height, color, title, subtitle):
    draw.rounded_rectangle((x, y, x + width, y + height), radius=28, fill='white', outline='#dce5ee', width=2)
    draw.rounded_rectangle((x + 28, y + 28, x + 37, y + 100), radius=4, fill=color)
    text(x + 58, y + 24, title, 39, color, True)
    text(x + 58, y + 81, subtitle, 25, MUTED)


def card(x, y, width, height, name, title, fields, color=BLUE):
    draw.rounded_rectangle((x, y, x + width, y + height), radius=18, fill='#ffffff', outline='#d9e3ed', width=2)
    draw.rounded_rectangle((x, y, x + width, y + 68), radius=18, fill='#edf4fc' if color == BLUE else '#eaf5f0')
    draw.rectangle((x + 2, y + 48, x + width - 2, y + 68), fill='#edf4fc' if color == BLUE else '#eaf5f0')
    title_size = 32 if len(name) < 25 else 28
    assert draw.textlength(name, font=font(title_size, mono=True)) <= width - 40, name
    text(x + 20, y + 13, name, title_size, color, mono=True)
    text(x + 22, y + 84, title, 28, INK, True)
    for index, field in enumerate(fields):
        assert draw.textlength(field, font=font(25)) <= width - 42, (name, field)
        text(x + 22, y + 132 + index * 37, field, 25, MUTED)
    assert 132 + max(0, len(fields) - 1) * 37 + 38 <= height, name


def arrow(points, color, dashed=False, label=None, label_at=None):
    for a, b in zip(points, points[1:]):
        if dashed:
            distance = math.dist(a, b)
            for start in range(0, int(distance), 24):
                end = min(start + 13, distance)
                draw.line([(a[0] + (b[0]-a[0])*start/distance, a[1] + (b[1]-a[1])*start/distance),
                           (a[0] + (b[0]-a[0])*end/distance, a[1] + (b[1]-a[1])*end/distance)], fill=color, width=4)
        else:
            draw.line([a, b], fill=color, width=4)
    a, b = points[-2:]
    angle = math.atan2(b[1]-a[1], b[0]-a[0])
    draw.polygon([b, (b[0]-17*math.cos(angle-.5), b[1]-17*math.sin(angle-.5)),
                  (b[0]-17*math.cos(angle+.5), b[1]-17*math.sin(angle+.5))], fill=color)
    if label:
        x, y = label_at
        box = draw.textbbox((x, y), label, font=font(22, True))
        draw.rounded_rectangle((box[0]-8, box[1]-5, box[2]+8, box[3]+5), radius=6, fill='white')
        text(x, y, label, 22, color, True)


text(70, 42, 'NODEVERSE  /  DATABASE STRUCTURE', 26, BLUE, True)
text(70, 96, '현재 DB 구성 한눈에 보기', 62, INK, True)
text(74, 184, '회원·관리자는 MySQL에, 플레이 기록과 문제 정의는 서버 MongoDB에 저장합니다.', 31, MUTED)
pill(2660, 62, '실제 스키마 확인 · 2026.11.09', BLUE, '#e5effb')

panel(60, 280, 1370, 1730, BLUE, 'MySQL  ·  회원 / 관리자', '10 TABLES  ·  인증과 회원 식별 정보')
panel(1540, 280, 1800, 1730, GREEN, 'MongoDB  ·  플레이 기록', '5 COLLECTIONS  ·  문제·시도·행동 이벤트')

card(90, 445, 620, 400, 'admin_accounts', '대시보드 관리자 계정', [
    'PK  admin_id  ·  관리자 UUID',
    'login_id / password_hash',
    'nickname / account_role',
    'created_at / last_login_at / updated_at',
    'is_active / is_staff / is_superuser',
    'email / first_name / last_name',
])
card(780, 445, 620, 400, 'game_members', '게임 회원 식별 정보', [
    'PK  member_id  ·  대시보드 회원 UUID',
    'UK  external_member_key  ·  외부 연결 키',
    'nickname  ·  회원 표시 이름',
    'data_source  ·  live / demo',
    'registered_at  ·  최초 등록 시각',
    '게임 비밀번호는 저장하지 않음',
])

text(100, 889, '관리자 권한 연결', 27, BLUE, True)
card(90, 945, 620, 190, 'admin_group_memberships', '관리자 → 권한 그룹', ['FK  user_id → admin_id / group_id'])
card(780, 945, 620, 190, 'auth_group', '권한 그룹 정의', ['PK  id / name'])
card(90, 1220, 620, 190, 'admin_permission_assignments', '관리자 → 개별 권한', ['FK  user_id → admin_id / permission_id'])
card(780, 1220, 620, 190, 'auth_permission', '허용 작업 목록', ['PK  id / codename / FK content_type_id'])
card(780, 1485, 620, 190, 'auth_group_permissions', '권한 그룹 → 개별 권한', ['FK  group_id / permission_id'])

# Solid arrows are real MySQL foreign-key references (child -> referenced parent).
arrow([(90, 1040), (73, 1040), (73, 730), (90, 730)], BLUE)
arrow([(710, 1040), (780, 1040)], BLUE)
arrow([(90, 1310), (68, 1310), (68, 780), (90, 780)], BLUE)
arrow([(710, 1315), (780, 1315)], BLUE)
arrow([(1110, 1485), (1110, 1410)], BLUE)
arrow([(1400, 1580), (1414, 1580), (1414, 1065), (1400, 1065)], BLUE)

draw.rounded_rectangle((90, 1485, 710, 1675), radius=18, fill='#f2f6fb')
text(112, 1505, '권한 관계 읽는 법', 27, BLUE, True)
text(112, 1555, '실선: 연결 테이블 → 참조 대상', 25, MUTED)
text(112, 1596, 'user_id는 관리자 admin_id를 참조', 25, MUTED)

text(100, 1720, 'Django 내부 관리  ·  게임 로그가 아닙니다', 27, BLUE, True)
system_tables = [
    ('django_session', '관리자 웹 로그인 유지', 'session_key / session_data / expire_date'),
    ('django_content_type', '모델 종류 · 권한 메타데이터', 'id / app_label / model'),
    ('django_migrations', 'DB 구조 변경 적용 이력', 'id / app / name / applied'),
]
for index, (name, meaning, fields) in enumerate(system_tables):
    y = 1780 + index * 66
    text(110, y, name, 27, BLUE, mono=True)
    text(475, y, meaning, 25, INK)
    text(910, y + 3, fields, 19, MUTED)

# MongoDB conceptual relationships: no cross-collection/cross-database SQL FK.
card(1580, 445, 770, 400, 'game_sessions', '게임 플레이 세션', [
    'PK  _id  ·  세션 UUID',
    'REF  player_id → game_members.member_id',
    'topic / level / game_version',
    'started_at / ended_at / status',
    'duration_ms  ·  전체 플레이 시간',
], GREEN)
card(2530, 445, 770, 400, 'game_problems', '콘텐츠 버전별 문제 정의', [
    'PK  _id  ·  문제 정의 UUID',
    'UK  task_id + content_version',
    'title / topic',
    'task_id는 사람이 읽는 문제 코드',
], GREEN)
card(2040, 980, 800, 400, 'problem_runs', '한 번의 문제 실행', [
    'PK  _id  ·  문제 실행 UUID',
    'REF  session_id → game_sessions._id',
    'REF  task_id → game_problems._id',
    'started_at / ended_at / status',
    'active_ms / paused_ms  ·  풀이·정지 시간',
], GREEN)
card(1580, 1530, 770, 390, 'solution_attempts', '문제 안의 개별 풀이 시도', [
    'PK  _id  ·  시도 UUID',
    'REF  run_id → problem_runs._id',
    'UK  run_id + number',
    'started_at / ended_at / outcome',
], GREEN)
card(2530, 1530, 770, 430, 'gameplay_events', '행동 · 실패 · 힌트 · 일시정지 로그', [
    'PK  _id / UK  session_id + sequence',
    'REF  session_id / run_id / attempt_id',
    'event_type / operation / failure_reason',
    'occurred_at / received_at',
    'state_before / state_after / payload',
    'hint_id / hint_step',
], GREEN)

arrow([(1960, 845), (1960, 905), (2220, 905), (2220, 980)], GREEN, True, '세션 1 : N 문제 실행', (1880, 876))
arrow([(2910, 845), (2910, 905), (2690, 905), (2690, 980)], GREEN, True, '문제 정의 1 : N 실행', (2720, 876))
arrow([(2220, 1380), (2220, 1455), (1965, 1455), (1965, 1530)], GREEN, True, '실행 1 : N 시도', (1880, 1424))
arrow([(2690, 1380), (2690, 1455), (2915, 1455), (2915, 1530)], GREEN, True, '실행 1 : N 이벤트', (2730, 1424))
arrow([(2350, 1720), (2530, 1720)], GREEN, True, '시도 1 : N', (2370, 1672))
arrow([(1400, 665), (1580, 665)], '#b07b24', True)
text(1442, 600, '1 : N', 26, '#946618', True)
text(1438, 705, 'UUID', 23, '#946618', True)

draw.rounded_rectangle((60, 2060, 3340, 2280), radius=24, fill='#e8eef5')
text(90, 2085, '연결 기준과 읽는 법', 31, INK, True)
text(90, 2142, 'MySQL member_id = MongoDB game_sessions.player_id  ·  게임 서버 원본 회원 ID와는 다른 대시보드 UUID입니다.', 28, INK)
text(90, 2190, '실선 = MySQL 외래 키 참조   |   점선 = UUID 논리 연결·1:N 관계   |   PK = 고유 ID   UK = 중복 방지 키   REF = 참조 ID', 27, MUTED)
text(90, 2234, 'MongoDB 관계는 수신 서버에서 검증합니다. 세션·문제·시도 UUID와 이벤트 순서로 연결하며, 시각은 UTC / 시간 값은 ms 단위입니다.', 25, MUTED)
text(70, 2302, '실제 스키마 기준 · MySQL 10개 테이블 / MongoDB 5개 컬렉션 · 게임 회원 수신과 플레이 기록 수집 API 연동', 23, MUTED)

destination = ROOT / 'output' / 'images' / 'NODEVERSE_현재_DB_구성_한장.png'
destination.parent.mkdir(parents=True, exist_ok=True)
image.save(destination, optimize=True, dpi=(180, 180))
print(destination)
