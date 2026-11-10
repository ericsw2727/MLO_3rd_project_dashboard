"""Create a shareable database connection and storage summary without secrets."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
im = Image.new('RGB', (2400, 2000), '#f2f5fa')
d = ImageDraw.Draw(im)
def txt(x, y, value, size=30, color='#26364c', bold=False):
    f = ImageFont.truetype('C:/Windows/Fonts/' + ('malgunbd.ttf' if bold else 'malgun.ttf'), size)
    d.text((x,y),value,font=f,fill=color)
def box(x,y,w,h):
    d.rounded_rectangle((x,y,x+w,y+h),radius=26,fill='white',outline='#dce3ee',width=2)
def row(x,y,name,desc,color):
    txt(x,y,name,31,color,True)
    txt(x,y+48,desc,27)

txt(90,65,'NODEVERSE  |  데이터베이스 구성',60,bold=True)
txt(94,153,'팀 공유용 · 비밀번호 제외 · 기존 확인 정보 기준',30,'#64748b')
box(80,225,2240,180)
txt(120,257,'DB 서버  192.168.0.167',39,bold=True)
txt(120,325,'송신 PC  192.168.0.81     /     대시보드 PC  192.168.0.29',31)

box(80,440,1095,1010)
box(1205,440,1115,1010)
blue,green='#285eb7','#168064'
txt(120,470,'MySQL  |  회원·관리자',43,blue,True)
txt(1245,470,'MongoDB  |  게임·행동 로그',43,green,True)
for x,lines in [(120,['DB  nodeverse     /     포트 3306','확인했던 버전  8.4.13','인증  계정·비밀번호 사용','적재 계정  nodeverse_ingest','비밀번호는 담당자에게 별도 전달']),
                (1245,['DB  nodeverse_logs     /     포트 27017','확인했던 버전  8.0.34','마지막 확인 기준  무인증 연결','URI  mongodb://192.168.0.167:27017/','적재 계정 생성·적용 완료는 미확인'])]:
    for i,line in enumerate(lines): txt(x,550+i*49,line,29)

row(120,835,'game_members','게임 회원 UUID · 외부 회원 ID · 닉네임 · 등록 시각',blue)
row(120,955,'admin_accounts','대시보드 관리자 계정',blue)
row(120,1075,'admin_group_memberships','관리자 그룹 연결',blue)
row(120,1195,'admin_permission_assignments','관리자 권한 연결',blue)
row(120,1315,'auth_* / django_*','권한 · 로그인 세션 · 마이그레이션 관리',blue)
for i,(name,desc) in enumerate([
    ('game_sessions','회원별 플레이 · 자료구조 · 레벨 · 시작/종료 · 상태'),
    ('game_problems','문제 코드 · 제목 · 콘텐츠 버전'),
    ('problem_runs','문제 풀이 · 실제 풀이 시간 · 일시정지 시간'),
    ('solution_attempts','풀이 시도 번호 · 시작/종료 · 성공/실패 결과'),
    ('gameplay_events','연산 · 실패 원인 · 상태 변화 · 힌트 · 정지/재개'),
]): row(1245,835+i*120,name,desc,green)

box(80,1480,2240,175)
txt(120,1505,'회원 연결 및 시간 규칙',33,bold=True)
txt(120,1560,'MySQL game_members.member_id  ↔  MongoDB game_sessions.player_id',31)
txt(120,1605,'회원 UUID로 연결  ·  시각은 UTC  ·  소요 시간은 밀리초(ms)',27,'#64748b')
box(80,1685,2240,245)
txt(120,1710,'적재 흐름 및 확인 사항',33,bold=True)
txt(120,1768,'Godot 게임 → 송신 측 Kafka / Spark → DB 직접 적재 → Django 대시보드',33)
txt(120,1827,'송신 측 MySQL 수정 대상은 game_members만 해당 · GAME_SERVER_API_KEY 미사용',28)
txt(120,1872,'실제 서버 적재·실시간 자동 연결은 검증 필요 · 계정 및 접속 허용은 별도 확인',28,'#a36516')
out=ROOT/'output/images/NODEVERSE_DB_정보_요약.png'
out.parent.mkdir(parents=True,exist_ok=True)
im.save(out,dpi=(180,180))
print('Created database summary PNG')
