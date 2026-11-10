# 데이터 이름 안내

이름 변경 마이그레이션은 기존 데이터와 UUID·관계를 보존합니다. SQL 컬럼은 읽기 쉽게 표시하고, Django 인증 필드와 공개 API 이름은 유지합니다.

| 이전 MySQL 테이블 | 변경 이름 | 의미 |
| --- | --- | --- |
| accounts_user → dashboard_admins | admin_accounts | 대시보드 관리자 (과거 learner 계정 포함) |
| accounts_user_groups → dashboard_admins_groups | admin_group_memberships | 관리자와 권한 그룹 연결 |
| accounts_user_user_permissions → dashboard_admins_user_permissions | admin_permission_assignments | 관리자 개별 권한 연결 |
| telemetry_player | game_members | 게임 회원의 대시보드 식별 정보 |
| telemetry_playsession | game_sessions | 한 번의 게임 플레이 |
| telemetry_learningtask | game_problems | 콘텐츠 버전별 문제 정의 |
| telemetry_taskrun | problem_runs | 문제를 시작해 종료하기까지의 실행 |
| telemetry_solveattempt | solution_attempts | 문제 실행 중 개별 풀이 시도 |
| telemetry_behaviorevent | gameplay_events | 연산·실패·힌트 등 행동 로그 |

`auth_*`, `django_*`는 Django가 사용하는 기본 테이블입니다. 특히 `django_session`은 관리자 웹 로그인 유지용입니다. 0005 적용 후 로그 테이블 5개는 MySQL에서 제거되며, 같은 이름의 MongoDB 컬렉션으로 관리됩니다. 회원과 관리자는 MySQL에 남습니다.

기본 테이블과 관리자 권한 연결 테이블에는 MySQL 테이블 설명(COMMENT)을 추가했습니다. 기존 도구 및 Django 동작을 유지하기 위해 기본 테이블의 물리 이름은 그대로 사용합니다.

## 게임 회원 컬럼

| MySQL 컬럼 | Django 필드 / 기존 컬럼 | 의미 |
| --- | --- | --- |
| member_id | id | 대시보드가 발급한 회원 UUID. 게임 회원 수신 API의 player_id |
| external_member_key | external_id | 외부 회원 연결 키. 예: game:member:원본회원ID |
| nickname | display_name | 게임 회원 표시 이름 |
| data_source | source | live: 실제, demo: 데모 |
| registered_at | created_at | 대시보드에 처음 등록된 시각 |

SQL의 member_id와 게임 서버 원본 회원 ID(API 요청의 member_id)는 다릅니다. MongoDB에는 대시보드 UUID를 player_id로 연결합니다.

## 관리자 컬럼

| MySQL 컬럼 | Django 필드 / 기존 컬럼 | 의미 |
| --- | --- | --- |
| admin_id | id | 관리자 UUID |
| login_id | username | 관리자 로그인 아이디 |
| password_hash | password | 해시 처리된 비밀번호. 평문 비밀번호 아님 |
| nickname | display_name | 관리자 표시 이름 |
| account_role | role | admin 또는 과거 learner |
| created_at | date_joined | 계정 생성 시각 |
| last_login_at | last_login | 마지막 로그인 시각 |
| updated_at | updated_at | 계정 최종 수정 시각 |

is_active(활성 계정), is_staff(Django 관리 권한 표식), is_superuser(전체 권한), email, first_name, last_name은 Django 기본 컬럼을 유지합니다. 실제 대시보드 접근은 기존처럼 role=admin 인증 검사에 따릅니다. 권한 연결 테이블의 user_id는 admin_accounts.admin_id를 참조합니다.

코드에서는 기존 Django 모델 클래스와 API 필드 이름을 유지해 연동을 보존합니다. 조회·회원 수신 코드의 지역 변수는 다음처럼 풀어 썼습니다.

| 이름 | 의미 |
| --- | --- |
| page_context | 화면에 전달하는 데이터 |
| filter_form / filters | 검증된 조회 조건 |
| average_duration_ms | 평균 플레이 시간 (밀리초) |
| session_counts_by_player | 플레이어별 세션 집계 |
| event_counts_by_player | 플레이어별 이벤트 집계 |
| game_member / member_profile | 저장된 회원 / 전달받은 회원 정보 |
| server_api_key | 게임 서버 인증 키 |
| admin_account / admin_form | 관리자 계정 / 관리자 입력 폼 |
| registration_data / registration_form | 가입 요청 / 가입 검증 폼 |
| request_data | 요청에서 읽은 데이터 |
| record_type / record_fields / validated_fields | 기록 종류 / 요청 필드 / 검증된 필드 |

공개 API의 `player_id`, `member_id`, `task_id`, 시간 단위 `_ms` 등은 기존 규약을 유지합니다. 과거 PDF·ZIP 문서는 이전 테이블 이름을 포함할 수 있으며 현재 이름은 이 문서와 Django 마이그레이션을 기준으로 확인합니다.
