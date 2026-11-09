from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import math
R=Path.cwd();W,H=2600,1950
im=Image.new('RGB',(W,H),'#f5f8fb');d=ImageDraw.Draw(im)
def font(n,b=False):return ImageFont.truetype('C:/Windows/Fonts/malgunbd.ttf' if b else 'C:/Windows/Fonts/malgun.ttf',n)
def t(x,y,s,n=27,c='#29445b',b=False):d.text((x,y),s,font=font(n,b),fill=c)
def box(x,y,w,h,title,sub,rows,color='#257d9a'):
 d.rounded_rectangle((x,y,x+w,y+h),radius=20,fill='white',outline='#dce5ed',width=2)
 d.rounded_rectangle((x+23,y+26,x+30,y+h-26),radius=3,fill=color)
 t(x+48,y+22,title,34,color,True);t(x+48,y+74,sub,22,'#7a8d9f')
 for i,row in enumerate(rows):t(x+48,y+116+i*38,row,25)
def arrow(points,c='#678b9d',width=5,dash=False):
 for a,b in zip(points,points[1:]):
  if dash:
   length=math.dist(a,b)
   for pos in range(0,int(length),23):
    end=min(pos+12,length);d.line([(a[0]+(b[0]-a[0])*pos/length,a[1]+(b[1]-a[1])*pos/length),(a[0]+(b[0]-a[0])*end/length,a[1]+(b[1]-a[1])*end/length)],fill=c,width=width)
  else:d.line([a,b],fill=c,width=width)
 a,b=points[-2:];v=math.atan2(b[1]-a[1],b[0]-a[0]);d.polygon([b,(b[0]-19*math.cos(v-.5),b[1]-19*math.sin(v-.5)),(b[0]-19*math.cos(v+.5),b[1]-19*math.sin(v+.5))],fill=c)
def label(x,y,s,n=22,c='#637d91'):
 b=d.textbbox((x,y),s,font=font(n));d.rounded_rectangle((x-7,y-4,b[2]+7,b[3]+7),radius=6,fill='#f5f8fb');t(x,y,s,n,c)
def zone(y,h,title,sub,c):
 d.rounded_rectangle((50,y,2550,y+h),radius=23,outline=c,width=2)
 t(80,y+18,title,30,c,True);t(700,y+22,sub,23,'#718697')
t(70,45,'NODEVERSE / REVISED ARCHITECTURE',25,'#176b57',True)
t(70,100,'게임 로그 파이프라인과 관리자 진단 서비스',49,'#18344f',True)
t(72,180,'게임은 로그를 전송하고, 서비스는 정제된 데이터를 읽어 진단합니다.',28,'#647e91')
zone(250,730,'01  게임 → 데이터 파이프라인','대시보드 서비스 서버를 경유하지 않는 독립 수집 경로','#327f9e')
# Main route
arrow([(540,470),(680,470)],'#327f9e');label(552,390,'HTTPS',21);label(552,420,'JSON',21)
arrow([(1150,470),(1290,470)],'#327f9e');label(1163,407,'이벤트 발행',21)
arrow([(1760,470),(1900,470)],'#9164ac');label(1773,407,'스트림 구독',21)
box(80,355,460,245,'Godot 게임','이벤트 생성 · 비동기 전송',['문제·시도·연산·실패·힌트','로컬 큐 · 전송 실패 시 재시도'],'#327f9e')
box(680,355,470,245,'로그 수집 게이트웨이','파이프라인 입구 / HTTP API',['요청 인증 · 스키마 검증','Kafka 발행 · 최소 접수 확인'],'#327f9e')
box(1290,355,470,245,'Apache Kafka','버퍼 · 전달 · 재처리',['행동 이벤트 토픽 보관','원본 저장과 분석이 각각 구독'],'#a17a35')
box(1900,355,570,245,'Apache Spark','PySpark / Structured Streaming',['중복·시간·스키마 정리','세션·문제·시도 재구성 / 지표 계산'],'#8057a5')
# Two destinations: preserve raw independently of processing.
arrow([(1525,600),(1525,730)],'#a17a35');label(1180,654,'Kafka Connect / MongoDB Sink',21,'#916b30')
box(1290,730,470,200,'MongoDB · 원본','raw_events',['원본 이벤트 보존 · 재분석 기반'],'#a17a35')
arrow([(2185,600),(2185,730)],'#8057a5');label(2220,650,'Spark Connector',21,'#8057a5')
box(1900,730,570,200,'MongoDB · 정제·집계','curated / metrics',['풀이 이력 · 기간·사용자·문제별 지표'],'#8057a5')
# Main premise, left of storage cards.
d.rounded_rectangle((80,700,1160,930),radius=18,fill='#e7eff4')
t(108,724,'게임으로 분석 결과를 보내지 않습니다.',30,'#24566e',True)
t(108,778,'게임은 분석 완료를 기다리지 않고 플레이를 계속합니다.',26)
t(108,823,'통신 접수 확인만 유지해 누락·재전송을 제어합니다.',26)
t(108,870,'점선 재분석: 필요할 때 MongoDB 원본을 Spark가 다시 처리',22,'#708a9b')
# Optional historical reread with small cross-free route above storage.
arrow([(1760,830),(1830,830),(1830,655),(1980,655),(1980,600)],'#a4afbb',3,True)
zone(1050,665,'02  관리자 분석·진단 서비스','정제 데이터 조회 → 프로그램·AI 진단 → 결과 저장·표시','#176b57')
# Context store and service
box(80,1160,460,230,'MySQL','계정 · 기준 데이터',['관리자 계정·권한','플레이어 식별 · 콘텐츠 정의'],'#327f9e')
box(680,1160,570,230,'관리자 서비스 서버','Django / ORM + PyMongo',['MongoDB 정제 데이터 조회','진단 작업 생성 · 결과 조회 API'],'#176b57')
arrow([(540,1275),(680,1275)],'#327f9e');label(551,1210,'기준 정보',21)
# Processed data flows down the right corridor into service.
arrow([(2185,930),(2185,1125),(965,1125),(965,1160)],'#8057a5');label(1450,1080,'정제 데이터 · 분석 지표 조회 결과',24,'#8057a5')
box(1460,1160,1010,230,'진단 작업 워커','프로그램 규칙 기반 진단 + AI 해석',['반복 실패·이탈 구간 탐지 / 근거에 기반한 개선 제안','데이터 기간 · 규칙 버전 · AI 모델 정보를 함께 기록'],'#176b57')
arrow([(1250,1250),(1460,1250)],'#176b57');label(1275,1185,'작업 요청',22,'#176b57')
# Persist results then serve the dashboard.
box(1460,1495,1010,170,'MongoDB · 진단 결과','diagnoses',['진단 결과 · 근거 지표 · 개선 제안 · 작업 상태'],'#8057a5')
arrow([(1965,1390),(1965,1495)],'#8057a5');label(2010,1420,'결과 저장',22,'#8057a5')
box(680,1495,570,170,'관리자 대시보드','Django Templates / Chart.js',['대상·기간 선택 · 진단 요청 · 결과 검토'],'#176b57')
arrow([(890,1390),(890,1495)],'#176b57');label(700,1418,'결과·화면 제공',21,'#176b57')
arrow([(1100,1495),(1100,1390)],'#72998a',3);label(1120,1418,'조회·요청',20,'#176b57')
arrow([(1460,1580),(1340,1580),(1340,1345),(1250,1345)],'#8057a5');label(1274,1455,'결과 조회',21,'#8057a5')
# Summary
d.rounded_rectangle((50,1770,2550,1880),radius=18,fill='#e7eee9')
t(80,1790,'역할 구분: Spark = 정제·수치 계산  /  프로그램·AI = 진단·해석  /  관리자 = 제안 검토·게임 개선 결정',27,'#295c48',True)
t(80,1835,'게임 로그 수집과 관리자 인증은 분리합니다. 브라우저는 DB에 직접 접속하지 않고 서비스 API를 사용합니다.',25,'#557462')
t(72,1907,'NODEVERSE · 목표 설계 이미지 · 분석 결과의 게임 자동 반환 경로 없음',21,'#7b8fa0')
out=R/'output/images/NODEVERSE_파이프라인_관리자진단_흐름도.png';im.save(out);print(out)

