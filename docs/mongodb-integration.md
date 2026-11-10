# MySQL 회원 + MongoDB 학습 기록

## 실제 저장 위치

| MySQL | MongoDB |
| --- | --- |
| game_members, admin_accounts, Django 인증·세션·마이그레이션 | game_sessions, game_problems, problem_runs, solution_attempts, gameplay_events |

기존 Django 로그 모델은 필드 검증과 화면 표시용 객체(`managed=False`)입니다. `.objects`로 SQL 로그를 조회·저장하지 않습니다. 실제 저장은 `telemetry.mongo`와 `telemetry.recording`의 PyMongo 코드가 담당합니다. 로그 UUID와 관계 UUID는 MongoDB에 표준 하이픈 포함 문자열로, 시각은 UTC BSON Date로 저장합니다. 서버는 `tz_aware=True`로 읽고 화면은 한국 시간으로 표시합니다.

## 설치·이전

1. `pip install -r requirements.txt`
2. `.env`에 `MONGODB_URI`, `MONGODB_DATABASE`, `GAME_SERVER_API_KEY` 설정
3. 실행 중인 앱과 수집 프로세스 중지 및 MySQL 백업
4. `python manage.py check_mongodb` (접속 및 고유·조회 인덱스 생성)
5. `python manage.py migrate`
6. `python manage.py runserver`

0005는 MySQL 로그를 같은 UUID로 복사하고 문서 전체를 비교한 다음에만 SQL 로그 테이블 5개를 제거합니다. MongoDB의 추가 문서는 보존합니다. 같은 ID의 내용·고유 키가 충돌하면 삭제 전에 실패합니다. 중단 후 SQL 테이블 삭제가 시작되기 전에는 같은 내용으로 재시도할 수 있습니다. MySQL DDL은 전체 트랜잭션이 아니므로 테이블 삭제 도중 DB 장애가 발생하면 백업과 마이그레이션 상태를 점검해 수동 복구해야 합니다. 자동 역방향 이전은 지원하지 않습니다.

세션·문제 실행·이벤트 시작 시각과 기간 필터의 기준은 기존과 동일합니다. 이벤트는 발생 시각, 문제 통계는 기간 안에 시작된 문제 실행을 기준으로 이후 결과까지 추적합니다. 회원 필터는 MySQL, 세션·이벤트·학습 통계·차트·CSV는 MongoDB 데이터를 사용합니다. MongoDB 장애 시 503을 반환하며 빈 데이터로 위장하지 않습니다. 회원 수신 API는 MongoDB와 독립적으로 동작합니다.

## 게임 서버 수집 API

`POST /api/game/records` — `Content-Type: application/json`, `Authorization: Bearer <GAME_SERVER_API_KEY>`.

키는 서버에만 보관합니다. 게임 서버가 회원 로그인을 검증한 후 호출하며, Unity에 직접 키를 배포하지 않습니다. 빈 키는 503, 잘못된 키는 401입니다. CSRF 쿠키나 관리자 세션은 사용하지 않습니다.

```json
{
  "record_type": "session",
  "data": {
    "id": "11111111-1111-4111-8111-111111111111",
    "player_id": "22222222-2222-4222-8222-222222222222",
    "topic": "stack",
    "started_at": "2026-11-09T10:00:00+09:00"
  }
}
```

| record_type | 주요 data 필드 |
| --- | --- |
| session | id, player_id, topic, started_at; 선택 level, game_version |
| problem | id, task_id(문제 코드), content_version, title, topic |
| run | id, session_id, task_id(**problem의 UUID**), started_at |
| attempt | id, run_id, number(1 이상), started_at |
| event | id, session_id, run_id, sequence(세션 안에서 1 이상), event_type, occurred_at; 시도·연산 이벤트에는 attempt_id |
| end_attempt | id, status(success/failure/abandoned), ended_at |
| end_run | id, status(completed/abandoned), ended_at |
| end_session | id, status(completed/abandoned), ended_at |

회원 수신 응답의 `player_id`를 `session.player_id`에 넣습니다. 게임 서버 원본 회원 ID는 여기 넣지 않습니다. `task_id`는 기존 규약을 유지하므로 problem에서는 문제 코드, run에서는 문제 정의 UUID입니다.

권장 호출 순서는 회원 수신 → problem 등록 → session 시작 → run 시작 → attempt 시작 → event 전송 → end_attempt → run의 종료 이벤트 전송 → end_run → end_session입니다. session/run/attempt 생성은 진행 중 상태만 허용합니다. problem은 `(task_id, content_version)`별로 UUID를 고정합니다. 재시도 시 모든 기록 ID와 순서를 재사용합니다.

event에는 `operation`, `failure_reason`, `state_before`, `state_after`, `hint_id`, `hint_step`, `payload`도 전달할 수 있습니다. 필드·이벤트 종류는 모델 정의 및 기존 2.0 이벤트 규약을 참고하세요. `received_at`은 서버가 생성합니다. 메타데이터는 JSON 객체이며 각각 16KB 이하, 전체 요청은 64KB 이하입니다. 비밀번호·비밀 키·인증 헤더 등은 로그에 넣을 수 없습니다.

응답은 `{"record_id":"UUID","created":true}`이며 최초 201, 동일 내용 재전송 200입니다. 종료 요청은 200과 `status: finalized`를 반환합니다. 충돌·관계·시간 오류는 400, 큰 본문 413, JSON 형식 이외는 415, 저장소 장애는 503입니다. 네트워크 오류·5xx는 같은 ID로 재시도합니다. 기록 변경은 종료 API만 지원합니다.

단독 MongoDB에서도 작동하도록 세션 문서의 원자적 잠금으로 앱의 기록·종료 처리를 직렬화합니다. 잠금은 장애 복구를 위해 2분 후 만료됩니다. 여러 컬렉션과 MySQL을 아우르는 원자적 트랜잭션은 없으므로 중간 실패는 재시도로 복구합니다. 컬렉션에 외부에서 직접 쓰면 앱 검증과 잠금을 우회하므로 앱의 수신 API를 사용하세요.

## 테스트·데모

`python manage.py test accounts telemetry`는 SQL 테스트 DB와 무작위 `nodeverse_test_<UUID>` MongoDB를 사용하며, 종료 시 해당 테스트 DB만 삭제합니다. 실제 개발 MongoDB에는 테스트 데이터를 쓰지 않습니다. `seed_observatory`와 데모 별칭 명령은 회원만 MySQL에, 모든 학습 문서는 MongoDB에 생성하며 기존 기록을 덮어쓰지 않습니다.

과거 PDF·ZIP 설계 문서는 이전 구조를 설명할 수 있습니다. 현재 동작은 이 문서와 코드·마이그레이션을 기준으로 확인하세요.
