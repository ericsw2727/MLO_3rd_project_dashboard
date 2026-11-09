from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import math
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/images/NODEVERSE_전체_데이터_흐름도.png'
W,H=2600,1920
im=Image.new('RGB',(W,H),'#f5f8fb');d=ImageDraw.Draw(im)
def font(size,bold=False):return ImageFont.truetype('C:/Windows/Fonts/malgunbd.ttf' if bold else 'C:/Windows/Fonts/malgun.ttf',size)
def text(x,y,s,size=26,color='#31445c',bold=False):d.text((x,y),s,font=font(size,bold),fill=color,spacing=12)
def center(x,y,s,size=23,color='#546b82',bold=False):
 box=d.textbbox((0,0),s,font=font(size,bold));text(x-(box[2]-box[0])/2,y,s,size,color,bold)
def line(points,color='#8496aa',width=5,dashed=False):
 for a,b in zip(points,points[1:]):
  if not dashed:d.line([a,b],fill=color,width=width)
  else:
   length=math.dist(a,b)
   for start in range(0,int(length),22):
    end=min(start+12,length)
    d.line([(a[0]+(b[0]-a[0])*start/length,a[1]+(b[1]-a[1])*start/length),(a[0]+(b[0]-a[0])*end/length,a[1]+(b[1]-a[1])*end/length)],fill=color,width=width)
 a,b=points[-2:];angle=math.atan2(b[1]-a[1],b[0]-a[0]);length=17
 d.polygon([b,(b[0]-length*math.cos(angle-.5),b[1]-length*math.sin(angle-.5)),(b[0]-length*math.cos(angle+.5),b[1]-length*math.sin(angle+.5))],fill=color)
def card(x,y,title,subtitle,items,color='#176c57',height=250,number=None):
 d.rounded_rectangle((x,y,x+500,y+height),radius=22,fill='white',outline='#dce5ee',width=2)
 d.rounded_rectangle((x+24,y+26,x+31,y+height-26),radius=3,fill=color)
 text(x+52,y+23,title,34,color,True)
 text(x+52,y+75,subtitle,21,'#77899b')
 for i,item in enumerate(items):text(x+52,y+121+i*39,item,25)
 if number:
  d.ellipse((x+441,y-19,x+481,y+21),fill=color)
  center(x+461,y-14,str(number),22,'white',True)
def label(x,y,s,size=22,color='#536c81'):
 box=d.textbbox((0,0),s,font=font(size));tw=box[2]-box[0]
 d.rounded_rectangle((x-10,y-6,x+tw+10,y+size+12),radius=8,fill='#f5f8fb');text(x,y,s,size,color)
text(80,55,'NODEVERSE',24,'#176c57',True)
text(80,103,'전체 데이터 수집 · 분석 · 개선 흐름',52,'#142d48',True)
text(82,185,'Godot에서 발생한 행동을 안전하게 수집하고, 분석 결과로 게임 경험을 개선합니다.',27,'#61788c')
d.rounded_rectangle((2110,60,2500,111),radius=24,fill='#e4eee8');center(2305,70,'목표 아키텍처 / 권장 구성',22,'#176c57',True)
# Pipeline connections
line([(580,420),(700,420)],'#258b72');center(640,352,'HTTPS',21);center(640,382,'JSON',21)
line([(1200,420),(1320,420)],'#258b72');center(1260,352,'Producer',20);center(1260,382,'발행',21)
line([(1820,420),(1940,420)],'#258b72');center(1880,352,'Kafka',20);center(1880,382,'Source',20)
# Metadata storage
line([(950,550),(950,930)],'#488db1');label(978,708,'Django ORM',24,'#327a9f');label(978,748,'관계형 데이터 저장',22,'#327a9f')
# Kafka raw log storage
line([(1570,550),(1570,650)],'#a37c35')
line([(1570,825),(1570,1055),(1940,1055)],'#a37c35');label(1588,970,'원본 로그 보관',23,'#926b2f')
# Spark aggregated output
line([(2190,550),(2190,930)],'#8a6bb2');label(2218,692,'MongoDB',24,'#805aa9');label(2218,732,'Spark Connector',22,'#805aa9');label(2218,772,'분석 결과 upsert',22,'#805aa9')
# Read path: arrows denote flow of records from stores into read API.
line([(950,1180),(950,1270),(1440,1270),(1440,1390)],'#488db1');label(985,1222,'관리자·플레이어·문제 정보',22,'#327a9f')
line([(2190,1180),(2190,1300),(1690,1300),(1690,1390)],'#8a6bb2');label(1840,1222,'원본 상세 + 분석 결과',22,'#805aa9')
line([(1320,1500),(1200,1500)],'#258b72');center(1260,1425,'JSON /',20);center(1260,1455,'HTML',20)
# Iterative feedback
line([(700,1510),(190,1510),(190,615),(330,615),(330,550)],'#aab6c2',4,True)
# Component cards
card(80,300,'Godot 게임','GDScript / HTTPRequest', ['문제·시도·조작 이벤트 생성','로컬 전송 큐 · 묶음 전송','실패 시 재시도 · event_id 유지'],number=1)
card(700,300,'Django 수집 API','HTTPS + JSON / REST API', ['설치·플레이어·세션 식별','요청 검증 · 식별 정보 매핑','Kafka 발행 확인 후 접수 응답'],number=2)
card(1320,300,'Apache Kafka','이벤트 전달 · 버퍼 · 재처리', ['행동 이벤트 토픽에 저장','플레이어 키로 파티션 분배','원본 저장 / 분석이 각각 구독'],color='#a37c35',number=3)
card(1940,300,'Apache Spark','PySpark / Structured Streaming', ['중복·시간·스키마 정리','문제·사용자·버전별 집계','해결률 · 재시도 · 포기 분석'],color='#8a6bb2',number=4)
card(1320,650,'Kafka Connect','MongoDB Sink Connector', ['Kafka → MongoDB 원본 적재'],color='#a37c35',height=175)
card(700,930,'MySQL','계정 · 식별 · 정형 데이터', ['관리자 계정 · 권한 · 웹 세션','플레이어 식별자 매핑','문제·콘텐츠 버전 정의'],color='#327a9f')
card(1940,930,'MongoDB','원본 로그 + 분석 결과', ['raw_events: 행동 로그 원본','analytics: Spark 집계 결과','event_id / 집계 키로 중복 방지'],color='#805aa9')
card(1320,1390,'Django 조회 API','Django ORM + PyMongo', ['MySQL·MongoDB 결과 조합','관리자 인증 · 필터 · 페이지 이동'],height=225)
card(700,1390,'관리자 대시보드','Django Templates / Chart.js', ['플레이어별 행동 타임라인','문제·버전별 비교 · 개선 판단'],height=225,number=5)
# Feedback note set away from vertical arrow
text(270,1080,'게임 개선',32,'#637588',True)
text(270,1136,'문제 · 설명 · 힌트 수정',23,'#637588')
text(270,1175,'수정 버전으로 다시 측정',23,'#637588')
# Common design notes
notes_y=1695
d.rounded_rectangle((80,notes_y,2500,1855),radius=20,fill='#eaf0f5')
text(112,1719,'핵심 연결 원칙',25,'#243f57',True)
text(112,1765,'게임은 DB에 직접 접속하지 않습니다.  |  player_id는 서버에서 결정합니다.  |  event_id로 재전송 중복을 제어합니다.',23,'#496279')
text(112,1806,'과거 로그 재분석: MongoDB 원본 → Spark 배치 분석 → 결과 갱신  |  대시보드는 매번 전체 원본을 계산하지 않고 집계 결과를 조회합니다.',22,'#496279')
text(82,1880,'NODEVERSE · TARGET DATA ARCHITECTURE · Godot / Django / Kafka / Spark / MySQL / MongoDB',17,'#8293a3')
im.save(OUT)
print(OUT)
