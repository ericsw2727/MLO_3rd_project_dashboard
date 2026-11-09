from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1]
W,H=3000,3580
im=Image.new('RGB',(W,H),'#f5f8fb');d=ImageDraw.Draw(im)
BLUE='#287ea7';PURPLE='#8054ad';INK='#18344f';MUTED='#647b90'
def f(size,bold=False):return ImageFont.truetype('C:/Windows/Fonts/malgunbd.ttf' if bold else 'C:/Windows/Fonts/malgun.ttf',size)
def t(x,y,s,size=28,color=INK,bold=False):
 assert d.textbbox((x,y),s,font=f(size,bold))[2]<W-35,(s,'overflow')
 d.text((x,y),s,font=f(size,bold),fill=color)
def card(x,y,w,h,title,subtitle,rows,color):
 d.rounded_rectangle((x,y,x+w,y+h),radius=22,fill='white',outline='#dce5ee',width=2)
 d.rounded_rectangle((x+26,y+26,x+33,y+h-26),radius=3,fill=color)
 t(x+57,y+22,title,34,color,True);t(x+57,y+77,subtitle,24,MUTED)
 for i,row in enumerate(rows):t(x+57,y+126+i*43,row,26)
def pill(x,y,w,title,color):
 d.rounded_rectangle((x,y,x+w,y+62),radius=15,fill=color);t(x+24,y+12,title,29,'white',True)
t(80,55,'NODEVERSE / DATA CONTRACT',26,'#176c57',True)
t(80,103,'MySQL · MongoDB 데이터셋 설계',58,INK,True)
t(82,192,'무엇을 저장하고, 어떤 형식으로 연결할까?  |  목표 아키텍처 기준 권장 데이터 계약',29,MUTED)
d.rounded_rectangle((80,263,2920,371),radius=18,fill='#e7eef4')
t(115,285,'Godot → HTTPS·JSON → Django 수집 API → Kafka → 원본 저장 / Spark 분석 → MongoDB',32,INK,True)
t(115,332,'MySQL: 관리자·식별·콘텐츠 기준 정보     |     MongoDB: 행동 원본·풀이 이력·분석 결과',24,MUTED)
pill(80,414,1380,'MySQL  /  관계형 기준 데이터',BLUE)
pill(1540,414,1380,'MongoDB  /  행동 문서와 분석 데이터',PURPLE)
# Dataset rows use logical names, not promises about already-deployed schemas.
card(80,510,1380,430,'01  관리자 계정 · 인증','입력: 관리자 가입·운영자 관리 → Django ORM → SQL 행',[
 'admin_id: UUID  |  login_id: VARCHAR(150), UNIQUE',
 'password_hash: VARCHAR(128)  |  display_name: VARCHAR(80)',
 'role: VARCHAR(16)  |  is_active: BOOLEAN',
 'created_at / updated_at: DATETIME(6), UTC',
 '웹 로그인 세션은 별도 세션 테이블로 관리',
 '게임에서 관리자 비밀번호·해시·권한 정보를 전송하지 않음'
],BLUE)
card(80,980,1380,350,'02  플레이어 식별 정보','입력: 서버가 확인한 게임 식별 정보 → 등록·매핑',[
 'player_id: UUID, PK  |  external_id: VARCHAR(150), UNIQUE',
 'display_name: VARCHAR(80)  |  source: live / demo',
 'created_at: DATETIME(6), UTC',
 '일반 플레이어의 웹 로그인 아이디·비밀번호는 없음',
 '설치 ID와 실제 사람은 구분 · 다른 기기 통합은 별도 정책'
],BLUE)
card(80,1370,1380,320,'03  문제 · 콘텐츠 버전 기준 정보','입력: 게임 제작팀이 등록하는 콘텐츠 정의',[
 'task_id: VARCHAR(80) + content_version: VARCHAR(30), UNIQUE',
 'title: VARCHAR(120)  |  topic / concept_id: VARCHAR',
 'difficulty: SMALLINT  |  goal / rule_code: VARCHAR',
 'tutorial_version / hint_version: VARCHAR  |  updated_at: UTC'
],BLUE)
card(80,1730,1380,360,'04  게임 세션 · 실행 ID 등록부','입력: 신뢰된 게임 세션 등록 요청 → 서버 발급·소유자 연결',[
 'session_id: UUID, PK  |  player_id: UUID, FK',
 'game_version / platform: VARCHAR  |  started_at: DATETIME(6)',
 'run_id: UUID → session_id + task_id + content_version',
 'attempt_id: UUID → run_id + 시도 번호 (INTEGER)',
 '여기는 ID·소유 관계의 기준 정보 · 반복 행동 원본은 MongoDB'
],BLUE)
card(1540,510,1380,430,'01  raw_events  /  행동 이벤트 원본','입력: Kafka → MongoDB Sink Connector  |  1이벤트 = 1문서',[
 '_id = event_id: UUID 문자열  |  schema_version: 문자열',
 'player_id / session_id / run_id / attempt_id: UUID 문자열',
 'sequence: 정수  |  event_type / operation / failure_reason: 문자열',
 'occurred_at / received_at: BSON Date (UTC)',
 'state_before / state_after / context: 객체  |  source: 문자열',
 'hint_id: 문자열, hint_step: 정수  |  사용하지 않는 필드는 생략',
 '원본은 보존 · player_id·received_at·source는 서버가 결정'
],PURPLE)
card(1540,980,1380,350,'02  task_runs · solve_attempts  /  풀이 이력','입력: Spark가 원본 이벤트를 재구성  |  실행·시도별 별도 문서',[
 'task_runs: run_id, player_id, session_id, task_id, content_version',
 'status: completed / abandoned / in_progress',
 'started_at / ended_at: Date  |  active_ms / paused_ms: 정수',
 'solve_attempts: attempt_id, run_id, number, outcome, 시작·종료',
 '관계는 ID로 연결 · 시도 배열을 무제한으로 한 문서에 쌓지 않음'
],PURPLE)
card(1540,1370,1380,320,'03  session_summaries  /  플레이 세션 요약','입력: Spark 집계 → session_id를 키로 갱신',[
 'session_id / player_id: UUID 문자열',
 'game_version / platform / end_reason: 문자열',
 'started_at / ended_at: Date  |  duration_ms / active_ms: 정수',
 'attempt_count / failure_count / hint_count: 정수 · 추적 범위 명시'
],PURPLE)
card(1540,1730,1380,360,'04  analytics  /  대시보드 분석 결과','입력: Spark → MongoDB Spark Connector  |  집계 키로 upsert',[
 '집계 키: 기간 + player/task/전체 구분 + 콘텐츠 버전 + source',
 'started_runs / solved_runs / abandoned_runs / retry_runs: 정수',
 'completion_rate / avg_active_ms: 실수 또는 null',
 'hint_evaluable / hint_next_success: 정수  |  metric_version: 문자열',
 'computed_at / window_start / window_end: Date · 시간대 명시'
],PURPLE)
# Actual formats examples
EX=2160
card(80,EX,1380,780,'저장 형식 예시  /  SQL 테이블의 1행','실제 저장은 컬럼 · 아래는 읽기 쉽게 JSON으로 표현',[],BLUE)
left=[
 '{',
 '  "player_id": "f1fd83bf-c168-4972-845c-a0242e860d20",',
 '  "external_id": "installation:server-verified-001",',
 '  "display_name": "노드 탐험가",',
 '  "source": "live",',
 '  "created_at": "2026-11-05T03:20:00Z"',
 '}',
 '',
 '권장 SQL 자료형',
 'UUID       → CHAR(32)  (현재 Django UUIDField 기준)',
 '문자열     → VARCHAR(n)',
 '참/거짓    → BOOLEAN',
 '시간       → DATETIME(6), UTC로 통일',
 '',
 '예: task_id="stack-03", content_version="1.1"',
 '문제·힌트·튜토리얼 버전은 제작팀이 등록합니다.'
]
for i,s in enumerate(left):t(137,EX+127+i*36,s,25,INK)
card(1540,EX,1380,780,'저장 형식 예시  /  raw_events 문서','전송 JSON → 서버 보강 → BSON 저장  |  날짜는 Extended JSON 표기',[],PURPLE)
right=[
 '{',
 '  "_id": "e1b2a4d7-4522-4c7e-a0e7-a1b7f8b0c8c1",',
 '  "schema_version": "2.0",',
 '  "player_id": "f1fd83bf-c168-4972-845c-a0242e860d20",',
 '  "session_id": "8b90317e-e46a-4f47-8fc0-4f602dc3cabf",',
 '  "run_id": "54b30eec-9157-485d-a2f4-73fce5d2c8b5",',
 '  "attempt_id": "cb80f3d9-1336-4cc1-b317-1c77102f985a",',
 '  "sequence": 3, "event_type": "operation_failed",',
 '  "operation": "pop", "failure_reason": "empty_stack",',
 '  "occurred_at": {"$date": "2026-11-05T03:20:00Z"},',
 '  "received_at": {"$date": "2026-11-05T03:20:01Z"},',
 '  "state_before": {"stack_size": 0},',
 '  "state_after": {"stack_size": 0},',
 '  "context": {"step_id": "pick-top", "input_method": "mouse"},',
 '  "source": "live"',
 '}'
]
for i,s in enumerate(right):t(1597,EX+127+i*36,s,25,INK)
# Connecting and measurement contracts
Y=3000
d.rounded_rectangle((80,Y,2920,3480),radius=22,fill='#e8eff5')
t(116,Y+25,'공통 규약  /  두 DB가 같은 플레이어·문제·실행을 가리키도록',32,INK,True)
notes=[
 '01  ID: API·Kafka·MongoDB는 UUID 문자열 통일. MySQL CHAR(32) 저장 시 하이픈 제거·복원은 서버에서 처리.',
 '02  출처: Godot은 이벤트와 서버 발급 실행 ID를 전송. 관리자 계정·집계 결과·player_id를 게임이 임의로 만들지 않음.',
 '03  시간: 전송은 RFC3339 UTC 문자열. MongoDB 저장 시 BSON Date로 변환. duration_ms는 밀리초 정수.',
 '04  중복: event_id를 문서 키로 사용. (session_id, sequence)도 유일하게 관리. 동일 ID의 다른 내용은 충돌로 처리.',
 '05  품질: 데이터셋별 schema_version·콘텐츠 버전·live/demo 분리. 문제 종료·시도·연산 결과는 서로 다른 이벤트.',
 '06  해석: 해결률 = 해결 실행 / 시작 실행. 힌트 후 성공은 평가 가능한 다음 시도만 집계. 분모가 없으면 null.',
 '07  최소 수집: 의미 있는 행동 때만 필요한 상태 저장. 비밀번호·토큰·실명·정밀 위치는 행동 로그에 넣지 않음.',
 '08  추가 확장: 단계·튜토리얼·힌트 노출, 종료 사유·기술 오류를 raw_events의 허용된 이벤트·context로 기록.'
]
for i,s in enumerate(notes):t(116,Y+88+i*43,s,26,'#486177')
t(82,3520,'NODEVERSE · TARGET DATASETS · 개념 데이터 계약이며 현재 로컬 MySQL 테이블을 변경하지 않습니다.',22,MUTED)
im.save(ROOT/'output/images/NODEVERSE_MySQL_MongoDB_데이터셋_설계.png')
print('Dataset diagram saved.')
