from pathlib import Path
import json,html
from reportlab.platypus import SimpleDocTemplate,Paragraph,Table,TableStyle,Spacer,Image,PageBreak
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'output/pdf'; DATA=ROOT/'docs/team_handoff'
pdfmetrics.registerFont(TTFont('KR','C:/Windows/Fonts/malgun.ttf'));pdfmetrics.registerFont(TTFont('KRB','C:/Windows/Fonts/malgunbd.ttf'))
S={
 'title':ParagraphStyle('title',fontName='KRB',fontSize=21,leading=30,spaceAfter=13,textColor=HexColor('#173d35'),wordWrap='CJK'),
 'h':ParagraphStyle('h',fontName='KRB',fontSize=12,leading=19,spaceBefore=12,spaceAfter=7,keepWithNext=True,textColor=HexColor('#176b57'),wordWrap='CJK'),
 'p':ParagraphStyle('p',fontName='KR',fontSize=9.2,leading=15,spaceAfter=7,wordWrap='CJK'),
 'cell':ParagraphStyle('cell',fontName='KR',fontSize=8,leading=12.6,wordWrap='CJK'),
 'code':ParagraphStyle('code',fontName='KR',fontSize=7.8,leading=12,spaceAfter=10,backColor=HexColor('#edf3f0'),borderPadding=8,wordWrap='CJK'),
 'meta':ParagraphStyle('meta',fontName='KR',fontSize=8,leading=13,spaceAfter=9,textColor=HexColor('#7b8b82'))}
def P(s,style='p'):return Paragraph(html.escape(str(s)).replace('\n','<br/>'),S[style])
story=[]
def title(s):story.extend([P('NODEVERSE / TEAM HANDOFF / 2026.11.05 / v0.1 검토 초안','meta'),P(s,'title')])
def h(s):story.append(P(s,'h'))
def p(s):story.append(P(s))
def code(s):story.append(P(s,'code'))
def table(headers,rows,widths=None):
 vals=[headers]+rows;n=len(headers); widths=widths or ([150,353] if n==2 else [110,180,213])
 t=Table([[P(v,'cell') for v in row] for row in vals],colWidths=widths,repeatRows=1,hAlign='LEFT')
 t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),HexColor('#e0ece5')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),('LINEBELOW',(0,0),(-1,-1),.4,HexColor('#dce5e0'))]));story.extend([t,Spacer(1,8)])
def page(s):story.append(PageBreak());title(s)
def footer(c,doc):
 c.setStrokeColor(HexColor('#d8e3dc'));c.line(46,42,549,42);c.setFont('KR',7.5);c.setFillColor(HexColor('#6f8177'));c.drawString(46,28,'NODEVERSE / 팀 공유용 / v0.1 검토 초안');c.drawRightString(549,28,str(doc.page))
def save(filename):
 doc=SimpleDocTemplate(str(OUT/filename),pagesize=(595.28,841.89),leftMargin=46,rightMargin=46,topMargin=42,bottomMargin=57,title=filename[:-4],author='NODEVERSE')
 doc.build(story,onFirstPage=footer,onLaterPages=footer);print(filename)

# Reference samples. No real identifiers or credentials.
event={'schema_version':'3.0','event_id':'e1b2a4d7-4522-4c7e-a0e7-a1b7f8b0c8c1','session_id':'8b90317e-e46a-4f47-8fc0-4f602dc3cabf','run_id':'54b30eec-9157-485d-a2f4-73fce5d2c8b5','attempt_id':'cb80f3d9-1336-4cc1-b317-1c77102f985a','sequence':3,'event_type':'operation_failed','occurred_at':'2026-11-05T03:20:00Z','operation':'pop','failure_reason':'empty_stack','state_before':{'stack_size':0},'state_after':{'stack_size':0},'context':{'step_id':'pick-top','game_version':'0.1.0','platform':'windows','input_method':'mouse'}}
batch={'batch_id':'d23a534a-9fb5-4e63-9c82-43a491ce89fb','events':[event]}
raw={**event,'_id':event['event_id'],'player_id':'f1fd83bf-c168-4972-845c-a0242e860d20','received_at':{'$date':'2026-11-05T03:20:01Z'},'occurred_at':{'$date':event['occurred_at']},'source':'demo','ingest_version':'gateway-0.1','task_id':'stack-03','content_version':'1.1'}
diagnosis={'diagnosis_id':'42ee28ad-74bc-4f0c-b71d-ae8112ec7632','status':'completed','scope':{'task_id':'stack-03','content_version':'1.1','source':'demo'},'window_start':'2026-11-01T00:00:00Z','window_end':'2026-11-06T00:00:00Z','input_snapshot_id':'snapshot-demo-001','metric_version':'1.0','rule_version':'0.1','prompt_version':'0.1','model_id':'example-model','findings':[{'code':'repeated_empty_stack','evidence':{'operation_failed':8,'observed_runs':12},'suggestion':'빈 스택 상태와 pop 불가 사유를 시각적으로 안내한다.'}],'human_review_status':'pending','requested_by':'a0f658a3-65ab-41e2-812c-d7f016ce8452','created_at':'2026-11-05T04:00:00Z','completed_at':'2026-11-05T04:00:10Z','as_of':'2026-11-05T03:59:00Z','ai_status':'completed'}
for filename,data in [('event-batch-v3.example.json',batch),('raw-event-v3.example.json',raw),('diagnosis.example.json',diagnosis)]:
 (DATA/filename).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')

# Document A
filenameA='NODEVERSE_팀공유_아키텍처_데이터셋_정의서.pdf'
title('아키텍처·데이터셋 정의서')
p('목적: Godot 게임의 행동을 수집·정제하고, 관리자 서비스가 프로그램·AI 진단을 수행하여 게임 개선에 활용한다. 이 문서는 구현 완료 보고서가 아닌 팀 연동을 위한 목표 설계다.')
story.append(Image(str(ROOT/'output/images/NODEVERSE_파이프라인_관리자진단_흐름도.png'),width=503,height=377.25))
h('읽는 기준')
p('확정 방향: Godot, Kafka, Spark, MongoDB를 사용한다. 게임 로그는 관리자 서비스와 분리된 수집 경로로 보낸다. 서비스는 정제 데이터를 읽어 진단하며 분석 결과를 게임에 자동 반환하지 않는다.')
p('권장 설계: 파이프라인 입구에 HTTP 게이트웨이를 둔다. 전송 접수 확인과 분석 응답은 구분한다. MySQL은 계정·기준 정보, MongoDB는 원본·정제·진단 결과를 맡는다.')
p('합의 필요: 아래 자료형·엔드포인트·제한·타임아웃·버전 3.0은 제안이다. 기존 로컬 규약 2.0을 자동 교체하지 않는다. 기존 PDF보다 이 문서의 목표 구조를 우선 검토한다.')
page('01. 시스템 경계와 팀 역할')
table(['영역','입력·처리','출력·책임'],[
 ['Godot','문제·시도·연산·도움·중단 이벤트 생성. 로컬 큐와 재시도','동일 event_id를 유지해 JSON 전송. DB 자격증명 보관 금지'],
 ['수집 게이트웨이','설치 자격·스키마·소유 관계 검사, 서버 필드 보강','Kafka 발행 접수. Django 관리자 서비스와 별도 실행·배포 경계'],
 ['Kafka / Connect','이벤트 토픽, 보관·재처리, 독립 소비자','원본 MongoDB 적재와 Spark 분석을 분리. 실패·지연 감시'],
 ['Spark','중복·지연·시간·이벤트 순서 정리, 문제·세션 재구성','정제 이력·버전별 지표. 키 기반 멱등 저장'],
 ['관리자 서비스','MySQL 인증, MongoDB 조회, 진단 작업 생성','진단 결과 API·화면. 브라우저의 DB 직접 접속 금지'],
 ['진단 워커','스냅샷 기준 규칙 진단 + AI 해석','근거·버전·상태를 포함한 diagnoses 저장. 게임 자동 수정 금지']])
h('4인 역할 분담안 - 실제 담당자는 팀에서 지정')
table(['역할','우선 산출물'],[
 ['A. 게임·계측','이벤트 발생 위치, 연산·실패 코드, 전송 큐, 콘텐츠 ID·버전 표'],
 ['B. 수집·플랫폼','설치 식별/자격 발급, 게이트웨이, Kafka·Connect, 원본 저장'],
 ['C. 데이터·진단','Spark 정제, 지표 사전, 진단 규칙·AI 입력/출력, 재처리 검증'],
 ['D. 관리자 서비스','관리자 인증, 조회·진단 API, 대시보드, MySQL 기준 정보 관리']])
h('함께 확인할 경계')
p('게임·수집 담당자는 JSON 샘플, 수집·데이터 담당자는 Kafka 메시지와 저장 BSON, 데이터·웹 담당자는 지표 분모와 진단 결과 샘플로 합동 검증한다. 인프라 버전 조합은 작은 호환성 테스트 후 고정한다.')
page('02. MySQL 데이터셋 정의')
p('원칙: 계정·콘텐츠·ID 소유 관계의 기준 저장소다. 아래는 논리 데이터셋이며 실제 테이블명은 Django 모델과 마이그레이션으로 결정한다. 반복 행동 원본과 분석 결과를 이중 기준 데이터로 관리하지 않는다.')
table(['데이터셋','필수 필드·권장 형식','생성·제약'],[
 ['관리자 계정','admin_id UUID; login_id VARCHAR(150); password_hash VARCHAR(128); display_name VARCHAR(80); role; is_active BOOLEAN; created_at/updated_at DATETIME(6)','관리자 가입/운영자 관리. 아이디 UNIQUE. 검증된 비밀번호 해시. 인증 세션 별도 테이블'],
 ['플레이어 등록부','player_id UUID; external_id VARCHAR(150); display_name VARCHAR(80); source live/demo; created_at DATETIME(6)','서버가 등록. external_id UNIQUE. 일반 웹 계정·비밀번호 없음. 설치 ID는 동일인 증거가 아님'],
 ['콘텐츠 기준 정보','task_id VARCHAR(80); content_version VARCHAR(30); title; topic; concept_id; difficulty; goal/rule_code; tutorial_version; hint_version','제작팀 등록. (task_id, content_version) UNIQUE. 수정은 새 버전. topic·실패 코드 목록을 함께 관리'],
 ['실행 ID 등록부','session_id → player_id; run_id → session_id + task_id + content_version; attempt_id → run_id + number; game_version; platform; started_at','게이트웨이가 소유 관계 등록·검사. (run_id, number) UNIQUE. 지표·이벤트 본문은 저장하지 않는 기준 레코드']])
h('식별 방식 권장안')
p('게임은 session/run/attempt에 UUIDv4 후보를 생성하고 시작 이벤트에서 등록을 요청한다. 게이트웨이가 인증된 설치에 매핑된 player_id를 결정하고 소유 관계를 검증·등록한다. 이벤트마다 사전 동기 ID 발급 응답을 기다리지 않도록 한다. 기존 이미지의 “서버 발급”은 이 등록·검증 방식으로 구체화한 제안이다.')
p('설치별 자격의 최초 발급·교체·폐기는 별도 등록 절차가 필요하다. 공통 비밀키를 게임 실행 파일에 넣지 않는다. 배포 플랫폼 결정 전까지 이 절차는 미확정이다.')
h('저장·참조 규칙')
p('API·Kafka·MongoDB에서는 하이픈 포함 UUID 문자열로 통일한다. MySQL은 현재 Django UUIDField 기준 CHAR(32)를 사용할 수 있으며 변환은 서버에서 한다. MySQL의 시간은 UTC DATETIME(6), 모든 표시 시각은 명시한 시간대로 변환한다. MongoDB와 MySQL 사이에는 DB 외래키가 없으므로 서비스가 참조 무결성을 검사한다.')
page('03. MongoDB 원본 이벤트 정의')
p('raw_events: 수집된 원본을 서버가 보강해 보존한다. 이벤트 1건당 문서 1개. 원본은 정제 결과로 덮어쓰지 않는다. 게임 전송 JSON과 MongoDB 저장 문서는 서버 필드·날짜형이 다르다.')
table(['필드','형식·내용','결정 주체'],[
 ['_id / event_id','동일 UUID 문자열. 재전송에도 유지','게임 생성 / 서버 검증'],
 ['schema_version','계약 버전 문자열. 제안 3.0','게임 / 게이트웨이 지원 버전 검사'],
 ['player_id / source','UUID / live 또는 demo','서버만 결정. 게임 입력 금지'],
 ['session_id','UUID. 이벤트가 속한 플레이 세션','게임 후보 / 서버 소유 검사'],
 ['run_id / attempt_id','문제 실행 / 풀이 시도 UUID. 이벤트 종류별 조건부 필수','게임 후보 / 서버 관계 검사'],
 ['task_id / content_version','문제와 콘텐츠 버전. task_started에서 검증 후 연결','게임 참조 / 서버 기준 정보 검증'],
 ['sequence','세션 단위 1부터 증가하는 정수. 재전송·새 배치에도 유지','게임'],
 ['event_type / operation','이벤트 종류 / 수행한 연산 코드','게임의 허용 코드 목록'],
 ['failure_reason','실패 원인 코드. 연산 실패 시 필수','게임 규칙 판단'],
 ['occurred_at / received_at','BSON Date UTC. 발생 시각 / 게이트웨이 최초 수신 시각','게임 / 서버'],
 ['state_before / state_after','필요한 상태만 담은 허용 JSON 객체','게임'],
 ['hint_id / hint_step','힌트 종류 문자열 / 1 이상 정수','게임'],
 ['context','단계, 플랫폼, 입력 방식, 게임·튜토리얼·힌트 버전 등 허용 필드','게임 / 서버 검증'],
 ['ingest_version / provenance','수집기 버전, 선택적 topic/partition/offset, 검증 상태','서버·파이프라인']],[105,230,168])
h('권장 인덱스와 저장 형식')
p('_id 고유, (session_id, sequence) 고유, (player_id, occurred_at), (task_id, content_version, occurred_at). raw_events는 source를 분리해 테스트 데이터가 실제 지표에 섞이지 않게 한다. 게임은 RFC3339 UTC 문자열을 보내며 저장 시 BSON Date로 변환한다. JSON의 $date 표기는 문서 예시용 Extended JSON이며 게임 요청 형식이 아니다.')
page('04. 정제·집계 데이터와 지표')
table(['컬렉션','내용·고유 키','생성 주체'],[
 ['task_runs','run_id 키; player/session/task/version; status; started_at/ended_at; active_ms/paused_ms; completeness','Spark가 원본 재구성'],
 ['solve_attempts','attempt_id 키; run_id; number; outcome; 시작·종료; completeness. 실행 안에 무제한 배열로 넣지 않음','Spark'],
 ['session_summaries','session_id 키; player_id; platform/game_version; 시작·종료; 종료 사유; 시간·문제·실패·힌트 수','Spark'],
 ['analytics','집계 범위·대상 ID·기간·콘텐츠 버전·source·metric_version의 복합 키. 분자·분모·계산 시각·스냅샷 ID','Spark']])
h('필수 지표 사전 - 제안 metric_version 1.0')
table(['지표','정의·주의'],[
 ['문제 해결률','해결된 문제 실행 / 시작한 문제 실행. 진행 중·불완전 시작도 분모 포함하되 별도 수를 표시'],
 ['문제 포기율','명시적 task_abandoned / 시작한 실행. 연결 끊김·타임아웃을 포기로 단정하지 않음'],
 ['재시도 실행','한 실행에 풀이 시도 2개 이상인 실행 수. 반복 이벤트 수와 구분'],
 ['평균 실제 풀이 시간','완료된 실행 중 계산 가능한 (종료-시작-정지 구간)의 평균. 누락·충돌 시간은 제외하고 제외 수 표시'],
 ['힌트 이후 다음 시도 성공','실행별 첫 힌트 뒤 시작한 바로 다음 시도 중 success/failure만 분모. success가 분자. 인과 효과로 해석하지 않음'],
 ['반복 실패 원인','operation_failed를 operation·failure_reason·문제 버전별 집계. attempt_failed와 중복 합산 금지']])
p('기간 계약: 문제 지표는 기간 내 시작한 실행 집단을 as_of 시각까지 추적한다. 이벤트 목록은 발생 시각 기준이다. 집계는 window_start 이상 window_end 미만이며 UTC 경계와 표시 시간대 Asia/Seoul을 함께 기록한다. 분모가 없으면 비율은 null, 관측 건수 0과 구분한다.')
h('지연·품질 표시')
p('as_of, computed_at, input_snapshot_id, incomplete_count, excluded_count를 결과에 포함한다. 늦은 로그로 값이 바뀌면 snapshot/revision을 바꾼다. source와 콘텐츠 버전이 다른 표본은 기본적으로 분리한다.')
page('05. 진단 결과·합의 항목·인수 기준')
h('추가 데이터셋: diagnoses')
p('최신 흐름도에 진단 워커가 추가되어, 기존 8개 논리 그룹에 진단 결과 그룹이 추가된다. MySQL 4그룹, MongoDB 5그룹이다. task_runs와 solve_attempts는 한 그룹이지만 별도 컬렉션이다.')
table(['필드 그룹','필수 내용'],[
 ['식별·상태','diagnosis_id, requested_by(admin_id), status queued/running/completed/failed, created_at/completed_at'],
 ['입력 범위·재현','대상·기간·source·content_version, input_snapshot_id, as_of, metric_version, rule_version'],
 ['AI 실행 정보','model_id, prompt_version, 실행 시각. 재실행은 새 diagnosis_id이며 모델 출력이 동일하다고 보장하지 않음'],
 ['결과·검토','findings: 코드·근거 수치·개선 제안·한계; human_review_status. AI 미사용/실패 상태도 명시']])
h('프로그램과 AI 경계')
p('Spark는 정제·수치 계산, 규칙 엔진은 임계 조건과 패턴 진단, AI는 근거를 바탕으로 설명·개선안을 작성한다. AI가 DB를 임의 변경하거나 게임에 자동 적용하지 않는다. 외부 AI로는 최소 집계 데이터만 보내고 실명·계정·토큰·원본 전체를 보내지 않는다. 모델·외부 전송 정책은 팀 합의가 필요하다.')
h('구현 전에 팀에서 결정할 항목')
table(['항목','결정 내용'],[
 ['게임 배포·등록','Godot 웹/데스크톱, 설치 자격 발급·갱신, 여러 기기 동일인 정책'],
 ['버전·운영','Godot/Kafka/Spark/Connector/MongoDB 호환 버전, 로컬·AWS 토폴로지'],
 ['부하·보관','전송 제한, 원본 보관 기간, Kafka retention, 이벤트 예상량, 삭제·익명화 정책'],
 ['분석·AI','지연 허용, 집계 주기, 포기·타임아웃 규칙, 최소 표본, 진단 규칙·모델·비용']])
h('인수 기준')
p('한 플레이어의 시작 → 실패 → 힌트 → 재시도 → 해결이 원본·정제·대시보드에서 같은 ID로 연결되어야 한다. 동일 배치를 재전송해도 횟수가 늘지 않아야 한다. demo/live가 분리되고 누락·지연·AI 실패가 화면에 표시되어야 한다. DB 직접 접속 키가 게임 빌드에 포함되면 안 된다.')
save(filenameA)

# Document B
story=[]
filenameB='NODEVERSE_팀공유_이벤트_파이프라인_연동규약서.pdf'
title('이벤트·파이프라인 연동 규약서')
p('버전 0.1 검토 초안. 이벤트 계약 3.0 제안이며 기존 로컬 2.0과 별개다. 아래 URL·제한·정책은 합의 후 구현한다. 현재 서버에 이 수집 API나 AI 진단 API가 존재한다는 의미가 아니다.')
h('1. 전송과 응답 원칙')
p('Godot은 파이프라인 수집 게이트웨이에 HTTPS POST + application/json; charset=utf-8로 전송한다. 관리자 웹 서비스와 일반 플레이어 로그인은 경유하지 않는다. 분석 완료·진단 결과를 게임으로 반환하지 않는다. HTTP 접수 확인만 전송 큐 관리에 사용한다.')
h('2. 공통 이벤트 필드')
table(['필드','형식 / 요구 조건'],[
 ['schema_version','필수 문자열 "3.0". 지원하지 않는 버전은 거부'],
 ['event_id / session_id','필수 UUIDv4 문자열. event_id는 이벤트당 유일, session_id는 한 플레이 세션'],
 ['sequence','필수 양의 정수. 세션 단위 증가. 재전송·배치 분할 시 바꾸지 않음'],
 ['event_type / occurred_at','허용 이벤트 문자열 / RFC3339 UTC 문자열, 예: 2026-11-05T03:20:00Z'],
 ['run_id / attempt_id','문제 이벤트에는 run_id. 시도·연산 이벤트에는 둘 다 필요. 세션 이벤트에서는 생략'],
 ['task_id / content_version','task_started에서 필수. 기준 콘텐츠와 일치해야 하며 이후 run_id로 참조'],
 ['operation / failure_reason','연산 이벤트에 operation. operation_failed에는 failure_reason도 필수'],
 ['state_before / state_after','객체. 실패 이벤트에서 필요한 상태 필수. 허용 키·크기 제한 적용'],
 ['hint_id / hint_step','hint 이벤트에서 필수. 문자열 / 1 이상 정수'],
 ['context','게임 버전, 단계, 플랫폼, 입력 방식 등 합의한 객체. 자유로운 개인정보 입력 금지'],
 ['금지 입력','player_id, source, received_at, 관리자 계정, 비밀번호, 토큰은 본문에 넣지 않음']])
h('ID 등록과 전송 순서')
p('설치별 자격은 별도 절차로 발급한다. 게임은 UUID 후보를 만들고 session_started → task_started → attempt_started 순서로 소유 관계를 등록한다. 첫 전달은 세션별 순서대로 직렬 전송한다. 재전송 중복·하위 파이프라인 역순 수신은 별도로 처리한다. event_id를 새로 발급해서 재시도하지 않는다.')
page('01. 이벤트 사전·상태 전이')
table(['종류','발생 시점','추가 필수·조건'],[
 ['session_started','게임 플레이 세션 시작','context.game_version/platform. 서버가 자격으로 player_id를 연결'],
 ['session_ended','종료를 감지한 시점','context.end_reason: user_exit/completed/error 등. 프로세스 강제 종료는 누락 가능'],
 ['task_started','문제에 진입','run_id, task_id, content_version. 다시 시작하면 새 run_id'],
 ['task_completed','문제의 목표를 충족','run_id. 성공 시도·해결 규칙과 일치'],
 ['task_abandoned','명시적으로 문제 포기','run_id, context.end_reason. 연결 끊김을 임의로 포기로 만들지 않음'],
 ['attempt_started','해결을 위한 새 풀이 시작','run_id, attempt_id, attempt_number. 같은 실행에서 1부터 증가'],
 ['attempt_succeeded / attempt_failed','해당 풀이의 결과 확정','run_id, attempt_id. 연산 결과와 의미가 다름'],
 ['operation_succeeded / operation_failed','push/pop 등 의미 있는 조작 결과','run_id, attempt_id, operation. 실패 시 원인·전후 상태'],
 ['hint','힌트를 실제 사용한 시점','run_id, hint_id, hint_step'],
 ['paused / resumed','문제 풀이 정지·재개','run_id. 중복 정지·선행 정지 없는 재개는 품질 오류'],
 ['step_entered / tutorial_viewed / hint_shown','단계 진입·설명 표시·힌트 노출','확장 이벤트. context.step_id 또는 tutorial/hint ID·버전'],
 ['technical_error / feedback_submitted','기술 오류·사용자 선택형 의견','확장 이벤트. error_code 또는 합의된 선택 코드. 자유 텍스트는 기본 미수집']],[130,170,203])
h('상태 전이와 시간 계산')
p('TaskRun: in_progress → completed 또는 abandoned. SolveAttempt: in_progress → success 또는 failure/abandoned. 같은 문제의 재시도는 run_id를 유지하고 attempt_id와 번호를 바꾼다. 연습 문제에 새로 진입하면 같은 task/version이어도 새 run_id다.')
p('active_ms = (종료-시작) - 정지 구간 합. 정지 중 종료되면 종료까지 정지로 계산한다. 로그가 누락되거나 시간 순서가 충돌하면 시간을 추측하지 않고 incomplete로 표시한다. 게임의 단조 증가 elapsed_ms를 추가하는 것은 향후 시간 동기화 보완안이다.')
page('02. HTTP 배치 계약·JSON 예시')
p('제안 주소: POST /ingest/v1/events. 경로 v1은 HTTP 인터페이스 버전, 이벤트 schema_version 3.0은 메시지 버전이다. 인증: Authorization: Bearer <설치 범위 자격>. 관리자 세션 쿠키·공통 게임 비밀키를 사용하지 않는다.')
p('초기 제안 제한: 배치 최대 100건, UTF-8 본문 최대 512KB, 개별 이벤트 최대 16KB. 온라인은 1~5초 단위로 묶고 명시적 종료 시 가능한 범위에서 flush한다. 수치는 부하 테스트 후 조정한다.')
code(json.dumps(batch,ensure_ascii=False,indent=2))
p('event-batch-v3.example.json은 전송 예시다. raw-event-v3.example.json은 player_id·source·수신 시각·문제 참조를 보강한 저장 예시다. 두 형식을 같은 요청으로 보내지 않는다. JSON 예시 값은 모두 가상 데이터다.')
page('03. 접수·실패·Kafka 저장 규약')
table(['응답·상황','게임·게이트웨이 처리'],[
 ['202 Accepted','배치의 모든 유효 이벤트가 Kafka broker ack를 받았을 때만 응답. DB 적재·분석 완료가 아님. accepted_event_ids와 batch_id 반환'],
 ['400 / 422','JSON 또는 이벤트 계약 오류. 자동 무한 재시도 금지. 오류 코드·이벤트 위치만 반환하고 원문·자격을 로깅하지 않음'],
 ['401 / 403','설치 자격·소유 관계 오류. 전송 중지·등록 절차 복구. 관리자 로그인으로 대체 금지'],
 ['413','배치 분할. 개별 이벤트 초과는 기록 포맷 수정. event_id·sequence 유지'],
 ['429 / 5xx / 네트워크 오류','로컬 큐 보존, 지수 백오프+무작위 지연. 1/2/4/8초, 최대 60초는 초기 제안'],
 ['부분 발행 후 오류','Kafka 배치가 전체 원자적이라고 가정하지 않음. 503이면 전체 배치 재전송 가능해야 함. downstream에서 event_id 중복 제거']])
h('202 예시 - 비즈니스 분석 응답이 아님')
code('{"batch_id":"d23a534a-9fb5-4e63-9c82-43a491ce89fb",\n "accepted_event_ids":["e1b2a4d7-4522-4c7e-a0e7-a1b7f8b0c8c1"]}')
h('Kafka 메시지와 소비자')
p('토픽 제안: nodeverse.behavior.raw.v3, nodeverse.behavior.quarantine.v3. 메시지 key는 서버 확정 player_id, value는 서버 보강 JSON이다. 동일 key의 파티션 내 전달 순서는 제공하되 여러 전송자·재전송·이벤트 시각까지 정렬된다고 가정하지 않는다.')
p('Producer는 acks=all과 idempotence를 사용하도록 검토한다. 이는 게임 재전송·DB 저장까지 자동 exactly-once가 된다는 뜻이 아니다. Kafka Connect 원본 적재와 Spark 정제는 독립 소비자 그룹으로 구성한다. Spark checkpoint와 connector offset을 영속 저장한다.')
h('중복·충돌·격리')
p('같은 event_id와 같은 의미 데이터는 한 번만 반영한다. received_at·Kafka offset 같은 전송 메타데이터는 의미 비교에서 제외한다. 같은 event_id의 다른 의미 내용 또는 (session_id, sequence)의 다른 이벤트는 충돌로 격리한다. 원본 문서를 last-write-wins로 조용히 덮어쓰지 않는다. MongoDB 고유 인덱스와 conflict 처리 동작을 connector 설정·별도 검증 단계에서 확인한다.')
page('04. Spark 정제·지표 재현·진단 API')
h('정제 단계')
p('스키마·코드 검사 → event_id 중복 처리 → player/session/run/attempt 참조 확인 → sequence·발생 시각 정렬 → 누락·지연 표시 → 상태 재구성 → 버전별 지표 집계 순서다. 지원하지 않는 이벤트는 무시하지 않고 격리·카운트한다.')
p('이벤트 시각과 received_at을 함께 저장하고 큰 시계 오차는 표시한다. 허용 지연 10분은 초기 제안이며, 그보다 늦은 데이터도 원본 보관 후 배치 재계산 대상으로 남긴다. watermark만으로 오래된 중복까지 영구 제거된다고 가정하지 않는다.')
p('집계는 stable key + metric_version + snapshot/revision으로 저장한다. micro-batch 재실행 시 단순 $inc로 누적하지 않는다. 같은 입력으로 실행을 반복해도 값이 같도록 전체 창 재계산 또는 원자적 revision 교체를 설계한다. 서로 다른 컬렉션의 갱신이 한 번에 보인다고 가정하지 않으며 조회에는 완료된 snapshot을 사용한다.')
h('관리자 진단 작업 API - 제안')
table(['요청','동작'],[
 ['GET /api/admin/metrics','대상·기간·source·콘텐츠 버전별 완료 snapshot 조회'],
 ['POST /api/admin/diagnoses','관리자 인증+CSRF 검사. 대상·기간·snapshot 선택. 202와 diagnosis_id 반환'],
 ['GET /api/admin/diagnoses/{id}','queued/running/completed/failed와 결과 조회. 관리자 권한 검사'],
 ['진단 워커','서비스가 snapshot을 전달해 작업 실행. 규칙 결과를 만든 후 AI에 최소 지표·근거만 제공']])
p('작업 큐 기술은 미확정이다. 서비스와 워커를 분리하는 비동기 작업 방식만 제안한다. 재실행은 새 diagnosis_id를 발급한다. AI 실패를 정상 완료로 표시하지 않고 규칙 진단의 성공 여부와 AI 실패를 구분한다.')
h('근거 있는 출력')
p('diagnosis.example.json에 출력 예시를 제공한다. 최소한 대상·기간·source·input_snapshot_id·metric/rule/prompt/model 버전·근거 수치·제안·한계를 포함한다. AI 입력은 로그에 포함된 지시문을 명령으로 실행하지 않으며, 모델 출력은 사람 검토 전 자동 배포하지 않는다.')
page('05. 버전·보안·합동 테스트')
h('계약 버전과 변경 절차')
p('문서 v0.1은 검토 초안, 이벤트 3.0은 새 목표 계약이다. 현재 로컬 event 2.0 및 SQL 저장 모델은 유지한다. 구현 착수 전 지원 버전·이벤트 코드·필수 필드를 팀이 승인하고, 알 수 없는 필드를 허용/거부할 정책을 명시한다. 기존 값 의미 변경·필수 항목 추가는 새 메시지 버전으로 배포하며 혼합 기간을 계획한다.')
h('개인정보·비밀값')
p('관리자 비밀번호·토큰·실명·정밀 위치를 이벤트에 넣지 않는다. context·state는 허용 키와 크기를 제한한다. 게임에 관리자 DB 키를 넣지 않으며 로그 수집 자격은 설치별 범위로 제한한다. 테스트는 source=demo와 가상 UUID만 사용한다. AI 외부 전송과 보관·삭제 기간은 구현 전 합의한다.')
h('팀 인수 테스트 시나리오')
table(['검증','통과 기준'],[
 ['정상 흐름','시작 → 실패 → 힌트 → 새 시도 → 성공이 같은 player/run으로 원본·정제·화면에 연결'],
 ['재전송·부분 실패','같은 이벤트·배치를 여러 번 보내도 카운트 동일. 발행 중간 오류 후 재시도 복구'],
 ['충돌·소유권','타 플레이어 session 재사용과 event_id 내용 변경은 거부·격리. 기존 원본 유지'],
 ['역순·누락·지연','순서 복원 또는 incomplete 표시. 재분석 후 snapshot 갱신. 강제 종료를 포기로 단정하지 않음'],
 ['시간·지표','60초 중 20초 정지는 active 40초. 시도 실패와 연산 실패를 중복 집계하지 않음. 0/0은 null'],
 ['버전·출처','같은 task의 1.0/1.1, live/demo가 기본 분리. 이전 이벤트로 새 문제 지표를 추측하지 않음'],
 ['진단','동일 snapshot 근거를 추적할 수 있음. AI 실패·검토 대기를 표시. 게임 자동 반환 없음']])
h('기술 참고 문서')
p('Godot HTTPRequest: https://docs.godotengine.org/en/stable/classes/class_httprequest.html\nKafka Producer: https://kafka.apache.org/39/configuration/producer-configs/\nSpark 처리·재실행 의미: https://spark.apache.org/docs/3.5.6/structured-streaming-programming-guide.html\nMongoDB 고유 인덱스: https://www.mongodb.com/docs/manual/core/index-unique/\n참고 문서는 동작 근거이며 제품 버전 고정안이 아니다. 실제 Spark/Kafka/Connector 호환 버전은 별도 합의한다.')
save(filenameB)
