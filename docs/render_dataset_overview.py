from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
R=Path.cwd();W,H=2200,2320
im=Image.new('RGB',(W,H),'#f5f8fb');d=ImageDraw.Draw(im)
def font(n,b=False):return ImageFont.truetype('C:/Windows/Fonts/malgunbd.ttf' if b else 'C:/Windows/Fonts/malgun.ttf',n)
def text(x,y,s,n=29,c='#233d54',b=False):d.text((x,y),s,font=font(n,b),fill=c)
def panel(x,y,title,subtitle,color):
 d.rounded_rectangle((x,y,x+990,y+125),radius=18,fill=color)
 text(x+30,y+18,title,39,'white',True);text(x+30,y+79,subtitle,24,'white')
def card(x,y,num,title,body,origin,color):
 d.rounded_rectangle((x,y,x+990,y+220),radius=18,fill='white',outline='#dde6ed',width=2)
 d.ellipse((x+25,y+25,x+75,y+75),fill=color);text(x+39,y+30,str(num),29,'white',True)
 text(x+95,y+24,title,33,color,True)
 for i,s in enumerate(body):text(x+30,y+90+i*41,s,28)
 text(x+30,y+177,'만드는 곳: '+origin,24,'#7a8c9b')
text(70,45,'NODEVERSE / 필요한 데이터셋 한눈에 보기',45,'#19374f',True)
text(72,120,'MySQL은 “누구·무엇”의 기준, MongoDB는 “어떻게 플레이했는가”의 기록',29,'#667f92')
panel(70,205,'MySQL · 기준 데이터 4종','관리·식별을 위해 정확하게 유지할 정보','#267f9e')
panel(1140,205,'MongoDB · 행동·분석 데이터 4종','게임에서 생긴 기록과 그 기록을 분석한 결과','#7d57a3')
left=[
 ('관리자 계정',['운영자 아이디 · 비밀번호 해시 · 이름 · 권한','관리자 웹 로그인에 사용'],'관리자 가입 / 서버'),
 ('플레이어 정보',['플레이어 ID · 표시 이름 · 게임 식별자','로그를 같은 플레이어에게 연결'],'등록 서버'),
 ('문제·콘텐츠 정보',['문제 ID · 자료구조 · 난이도 · 목표 · 버전','문제·설명·힌트의 기준과 버전 관리'],'게임 제작팀'),
 ('실행 ID·소유 관계',['세션 ID → 플레이어 / 문제 실행 ID → 문제','풀이 시도 ID → 문제 실행 연결'],'등록 서버')]
right=[
 ('행동 이벤트 원본',['언제 · 어느 문제에서 · 무엇을 했고 · 결과가 어땠는지','시도·연산·실패·힌트·정지·종료 등을 한 건씩 기록'],'Godot → 수집 API → Kafka'),
 ('문제 풀이·시도 이력',['문제별 시작·해결·포기 / 시도별 성공·실패','재시도 횟수 · 실제 풀이 시간 · 힌트 이용'],'Spark가 원본을 재구성'),
 ('플레이 세션 요약',['접속·종료 시각 · 플레이 시간 · 종료 사유','세션별 문제 수 · 실패 수 · 힌트 수'],'Spark가 원본을 요약'),
 ('대시보드 분석 결과',['해결률 · 포기율 · 반복 실패 원인 · 버전별 차이','플레이어별·문제별·기간별 지표'],'Spark가 집계')]
for i,(a,b,o) in enumerate(left):card(70,365+i*247,i+1,a,b,o,'#267f9e')
for i,(a,b,o) in enumerate(right):card(1140,365+i*247,i+1,a,b,o,'#7d57a3')
Y=1400
d.rounded_rectangle((70,Y,2130,Y+530),radius=20,fill='#e8f0ed')
text(102,Y+26,'그럼 Godot 게임에서는 무엇을 보내야 할까?',35,'#20604d',True)
text(102,Y+91,'게임은 아래 6가지를 이벤트로 전송합니다. 위 데이터셋 8종을 모두 직접 보내는 것은 아닙니다.',27,'#476c5d')
rows=[
 ('① 실행 식별','세션 ID · 문제 실행 ID · 풀이 시도 ID · 이벤트 ID · 순서'),
 ('② 문제와 시점','발생 시각 · 문제 내 단계 · 게임 버전 (문제 버전은 등록 정보에 연결)'),
 ('③ 실제 행동','문제 시작 · 연산 · 시도 결과 · 문제 해결 또는 포기'),
 ('④ 실패 상황','어떤 연산이 왜 실패했는지 · 필요한 조작 전후 상태'),
 ('⑤ 도움과 중단','힌트·설명 노출 / 사용 · 일시정지·재개 · 종료 사유'),
 ('⑥ 기술 환경','플랫폼 · 입력 방식 · 로딩 지연 · 오류 코드 (필요할 때만)')]
for i,(label,body) in enumerate(rows):
 yy=Y+150+i*54
 text(108,yy,label,28,'#20604d',True);text(400,yy,body,27,'#365d4e')
Y2=1985
d.rounded_rectangle((70,Y2,2130,Y2+215),radius=18,fill='white',outline='#dde6ed',width=2)
text(102,Y2+25,'연결의 핵심',31,'#19374f',True)
text(102,Y2+85,'같은 플레이어 ID · 문제 ID+버전 · 실행 ID로 두 DB의 데이터를 연결합니다.',29)
text(102,Y2+139,'Godot은 HTTPS·JSON으로 전송 → 서버가 신원·실행을 검증 → Kafka → 원본 저장·Spark 분석',27,'#667f92')
text(72,2250,'목표 설계 요약 · 일반 플레이어 웹 로그인 불필요 · 현재 DB 구조를 변경하지 않은 설명용 이미지',23,'#7a8c9b')
out=R/'output/images/NODEVERSE_필수_데이터셋_한눈에.png';im.save(out);print(out)
