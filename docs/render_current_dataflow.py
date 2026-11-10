"""One-page architecture of confirmed reads and the agreed direct-loading path."""
from pathlib import Path
import json
import math
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
state = json.loads((ROOT / 'docs/current_dataflow_snapshot.json').read_text(encoding='utf-8'))
assert state['mysql_host'] == state['mongodb_host'] == '192.168.0.167'
assert 'game_members' in state['mysql_tables']
assert set(['game_sessions','game_problems','problem_runs','solution_attempts','gameplay_events']) <= set(state['mongodb_collections'])
W, H = 3600, 2380
image = Image.new('RGB', (W, H), '#f5f6fb')
draw = ImageDraw.Draw(image)
INK, MUTED = '#25334b', '#748099'
BLUE, GREEN, PURPLE, AMBER = '#4274b7', '#298d76', '#8161bc', '#bf8b40'


def font(size, bold=False):
    return ImageFont.truetype('C:/Windows/Fonts/' + ('malgunbd.ttf' if bold else 'malgun.ttf'), size)


def text(x, y, value, size=27, color=INK, bold=False):
    draw.text((x,y), value, font=font(size,bold), fill=color)


def label(x, y, value, color=BLUE, size=22):
    box = draw.textbbox((x,y), value, font=font(size,True))
    draw.rounded_rectangle((box[0]-8,box[1]-5,box[2]+8,box[3]+5),radius=6,fill='#f5f6fb')
    text(x,y,value,size,color,True)


def arrow(points, color=BLUE, dashed=False, head=True, width=5):
    for a,b in zip(points,points[1:]):
        distance = math.dist(a,b)
        if dashed:
            for start in range(0,int(distance),25):
                end=min(start+13,distance)
                draw.line([(a[0]+(b[0]-a[0])*start/distance,a[1]+(b[1]-a[1])*start/distance),
                           (a[0]+(b[0]-a[0])*end/distance,a[1]+(b[1]-a[1])*end/distance)],fill=color,width=width)
        else:
            draw.line([a,b],fill=color,width=width)
    if head:
        a,b=points[-2:]
        angle=math.atan2(b[1]-a[1],b[0]-a[0])
        draw.polygon([b,(b[0]-20*math.cos(angle-.5),b[1]-20*math.sin(angle-.5)),
                      (b[0]-20*math.cos(angle+.5),b[1]-20*math.sin(angle+.5))],fill=color)


def zone(x,y,w,h,number,title,subtitle,color):
    draw.rounded_rectangle((x,y,x+w,y+h),radius=27,fill='#ffffff',outline='#e1e5ee',width=2)
    draw.rounded_rectangle((x+29,y+28,x+87,y+86),radius=15,fill=color)
    text(x+43,y+35,number,30,'white',True)
    text(x+110,y+28,title,36,color,True)
    text(x+32,y+105,subtitle,24,MUTED)


def card(x,y,w,h,title,subtitle,rows,color=BLUE,tint='#eef3fa',size=27):
    draw.rounded_rectangle((x,y,x+w,y+h),radius=18,fill='#fff',outline='#dce3ef',width=2)
    draw.rounded_rectangle((x,y,x+w,y+77),radius=18,fill=tint)
    draw.rectangle((x+2,y+55,x+w-2,y+77),fill=tint)
    text(x+25,y+15,title,35,color,True)
    assert draw.textlength(title,font=font(35,True))<w-50,title
    text(x+25,y+95,subtitle,23,MUTED)
    for i,row in enumerate(rows):
        assert draw.textlength(row,font=font(size)) < w-50,(title,row)
        text(x+25,y+143+i*45,row,size,INK)
    assert 143+(len(rows)-1)*45+43<=h,title


text(70,45,'NODEVERSE  /  CURRENT DATA ARCHITECTURE',27,PURPLE,True)
text(70,100,'게임 데이터가 대시보드에 도착하기까지',61,INK,True)
text(75,194,'송신 측 정제 → 검증·직접 DB 적재 → Django 조회·집계 → 관리자 대시보드',32,MUTED)
draw.rounded_rectangle((2850,56,3525,123),radius=23,fill='#ebe6f6')
text(2880,71,'현재 코드·DB 연결 기준 · 2026.11.09',26,PURPLE,True)

zone(60,310,1120,1710,'01','송신 측 · 게임 / 데이터 파이프라인','192.168.0.81  ·  상대방이 전달한 구성',AMBER)
zone(1390,310,940,1710,'02','서버 PC · 데이터 저장','192.168.0.167  ·  DB 연결 확인',GREEN)
zone(2540,310,1000,1710,'03','내 PC · 조회 / 시각화','192.168.0.29  ·  Django 실행',PURPLE)

card(95,485,1050,210,'게임 / 게임 서버','로그인 검증과 원본 학습 이벤트 생성',[
    '회원 식별 정보 · 스택 / 큐 / 트리 플레이 기록',
],AMBER,'#faf2e6')
card(95,815,470,235,'Apache Kafka','송신 측 수집·전달',[
    '이벤트 메시지 전달',
    '송신 측 운영 영역',
],AMBER,'#faf2e6',24)
card(675,815,470,235,'Apache Spark','송신 측 처리·정제',[
    '필드 정리 · 변환',
    '정제 결과 생성',
],AMBER,'#faf2e6',24)
card(95,1260,1050,355,'검증 · 직접 DB 적재 프로그램','전달 ZIP의 pipeline/direct/loader.py',[
    '회원 UUID 매핑 · 필수 필드 / 참조 / 중복 검증',
    '회원 정보 → MySQL / 문제·플레이 기록 → MongoDB',
    '동일 ID 재시도 · 진행표 보존 · 부분 실패 후 재개',
    '현재는 JSON 계획 적재기 · 스트림 자동 연결은 준비 단계',
],AMBER,'#faf2e6')
arrow([(620,695),(620,750),(330,750),(330,815)],AMBER,True)
label(350,712,'원본 이벤트',AMBER,23)
arrow([(565,930),(675,930)],AMBER,True)
arrow([(910,1050),(910,1150),(620,1150),(620,1260)],AMBER,True)
label(220,1100,'정제 출력 → 필드 매핑 → 적재 계획',AMBER,25)

draw.rounded_rectangle((95,1710,1145,1960),radius=17,fill='#faf7f0')
text(120,1734,'실제 적재 전 남은 확인',29,AMBER,True)
for i,row in enumerate([
    '송신 PC 계정·접속 허용 확인',
    '이벤트별 attempt_id 규칙 / active_ms·paused_ms 계산 합의',
    '테스트 회원 1명 → 기록 1세트 → 대시보드 표시 검증',
    'Kafka·Spark 출력과 적재기의 실시간 연결은 아직 미검증',
]):text(120,1790+i*38,row,25,MUTED)

card(1425,485,870,425,'MySQL · nodeverse','3306 / 회원·관리자·웹 인증 정보',[
    'game_members — 게임 회원 식별 정보',
    'admin_accounts — 대시보드 관리자',
    '권한 연결 테이블 / Django 내부 관리 테이블',
    'member_id — 대시보드 회원 UUID, CHAR(32)',
    'django_session — 관리자 웹 로그인 유지',
],BLUE,'#edf3fb')
card(1425,1150,870,575,'MongoDB · nodeverse_logs','27017 / 문제 정의·학습 기록·행동 이벤트',[
    'game_sessions — 플레이 세션 / player_id',
    'game_problems — 문제 코드·버전·정의 UUID',
    'problem_runs — 문제 실행·풀이·일시정지 시간',
    'solution_attempts — 풀이 시도와 결과',
    'gameplay_events — 연산·실패·힌트·상태 변화',
    '시각: UTC BSON Date / 시간 길이: 밀리초',
    'UUID 및 참조 ID: 하이픈 포함 문자열',
],GREEN,'#eaf5ef',25)
arrow([(1860,910),(1860,1150)],'#a9a1b7',True,False,3)
label(1510,970,'회원 UUID 논리 연결', '#8e819e',24)
label(1510,1020,'MySQL member_id = MongoDB player_id', '#8e819e',23)

arrow([(1145,1375),(1265,1375),(1265,665),(1425,665)],AMBER,True)
label(1180,596,'회원 정보',AMBER,22)
label(1180,632,'SQL / 3306',AMBER,20)
arrow([(1145,1480),(1425,1480)],AMBER,True)
label(1185,1405,'정제 기록',AMBER,22)
label(1185,1443,'27017',AMBER,20)

draw.rounded_rectangle((1425,1810,2295,1955),radius=16,fill='#f2f5f9')
text(1450,1834,'역할별로 저장소 분리',28,GREEN,True)
text(1450,1884,'회원과 인증은 MySQL / 학습 기록은 MongoDB',25,MUTED)

card(2575,675,930,630,'Django 대시보드 서버','127.0.0.1:8000 / 현재 개발 PC 로컬 웹 접속',[
    'Django ORM → MySQL 회원 조회',
    'PyMongo → MongoDB 학습 기록 조회',
    '회원 UUID 연결 · 기간 / 게임 / 플레이어 필터',
    '해결률 · 실패 · 힌트 · 풀이 시간 지표 집계',
    '화면 렌더링 · 차트 데이터 · CSV 내보내기',
    '관리자 인증·웹 세션은 MySQL 읽기 / 쓰기',
    '직접 적재 경로에서는 별도 수신 API 미사용',
],PURPLE,'#f0ebf8',27)
card(2575,1625,930,290,'관리자 브라우저','대시보드 · 플레이어 분석 · 행동 로그 조회',[
    '종합·게임별·개인별 분석 / 차트·테이블',
    '검색 · 정렬 · 날짜 선택 · CSV 다운로드',
    '게임 로그는 조회하고, 새 적재는 송신 측이 담당',
],PURPLE,'#f0ebf8',26)

arrow([(2295,650),(2420,650),(2420,855),(2575,855)],BLUE)
label(2345,670,'회원 조회',BLUE,22)
arrow([(2575,955),(2485,955),(2485,785),(2295,785)],BLUE)
label(2340,905,'인증·세션 저장',BLUE,21)
arrow([(2295,1410),(2420,1410),(2420,1155),(2575,1155)],GREEN)
label(2350,1300,'기록 조회',GREEN,22)
arrow([(2825,1305),(2825,1625)],PURPLE)
label(2620,1450,'HTML · JSON · CSV 응답',PURPLE,22)
arrow([(3255,1625),(3255,1305)],PURPLE)
label(3090,1450,'로그인 · 조회 요청',PURPLE,22)

draw.rounded_rectangle((60,2080,3540,2300),radius=25,fill='#eaeef6')
text(90,2103,'연결 상태를 구분해서 읽어주세요',30,INK,True)
arrow([(100,2175),(205,2175)],BLUE,width=4)
text(225,2157,'실선: 확인된 DB 조회·웹 요청과 응답',25,INK)
arrow([(1080,2175),(1185,2175)],AMBER,True,width=4)
text(1205,2157,'주황 점선: 송신 경로 / 실제 서버 적재·자동 연결 미검증',25,INK)
arrow([(2580,2175),(2685,2175)],'#a9a1b7',True,False,3)
text(2705,2157,'회색 점선: UUID 논리 참조',25,INK)
text(95,2230,'현재 선택한 방식: Kafka·Spark 처리 결과를 DB에 직접 적재. GAME_SERVER_API_KEY는 이 경로에 사용하지 않습니다.',27,MUTED)
text(72,2332,'확인 근거: 현재 Django 코드·.env의 비밀값 제외 연결 설정·DB 접속 확인·송신 측 전달 ZIP의 시작 안내와 필드 매핑',23,MUTED)

output = ROOT / 'output/images/NODEVERSE_현재_데이터흐름_아키텍처.png'
output.parent.mkdir(parents=True,exist_ok=True)
image.save(output,optimize=True,dpi=(180,180))
print(output)
