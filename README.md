# NODEVERSE

스택·큐·트리 학습 게임의 플레이 기록을 분석하는 **Django 기반 관리자 대시보드**입니다. 플레이어의 문제 풀이, 재시도, 연산 실패, 힌트 사용과 풀이 시간을 조회하고 비교합니다.

## 구현 현황

- 관리자 초대 코드 기반 가입, 로그인·로그아웃, 세션 인증 및 CSRF 보호
- 전체 종합 / 게임별 / 플레이어별 분석 화면
- 기간, 실제·데모 데이터, 자료구조, 플레이어, 문제 ID, 콘텐츠 버전 필터
- 플레이어 목록·상세, 행동 이벤트 조회 및 페이지네이션
- 문제 해결·포기·재시도·힌트·실패 원인·풀이 시간 분석과 차트
- 문제 실행 기록 CSV 내보내기
- 관리자 전용 조회 API와 합성 데모 데이터 생성 명령
- 데이터 모델, 이벤트 규약, SQL 참고 자료 및 팀 공유 문서

**현재 실행 애플리케이션은 Django + MySQL 구성입니다.** Unity 클라이언트, 외부 이벤트 수집 API, MongoDB 저장소와 파이프라인 진단 연동은 이 저장소에서 구현된 기능이 아닙니다. `docs/team_handoff`의 이벤트 규약 3.0은 팀 검토용 제안이며, 배포된 API 명세나 기존 2.0 규약의 대체물이 아닙니다.

## 기술 구성

| 구분 | 사용 기술 |
| --- | --- |
| 서버 | Python, Django 5.2 |
| 데이터베이스 | MySQL, mysqlclient |
| 화면 | Django Templates, CSS, JavaScript |
| 환경 설정 | python-dotenv |
| 문서 생성 | ReportLab (별도 의존성) |

정확한 애플리케이션 의존성 버전은 [requirements.txt](requirements.txt)를 참고하세요.

## 로컬 설치 및 실행

아래 명령은 Windows PowerShell 기준입니다. Python과 MySQL 서버가 필요하며, `mysqlclient` 설치 시 환경에 따라 빌드 도구 또는 MySQL 클라이언트 개발 라이브러리가 필요할 수 있습니다.

### 1. 가상환경 및 의존성

프로젝트 루트에서 실행합니다.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

이미 `.env`가 있으면 복사 명령을 건너뛰고 기존 설정을 확인하세요.

### 2. 환경 변수

`.env`에 로컬 환경 값을 입력합니다. 실제 비밀번호와 비밀 키는 Git에 올리지 않습니다.

| 변수 | 설명 |
| --- | --- |
| `DJANGO_SECRET_KEY` | 필수. 로컬에서 생성한 임의의 비밀 키 |
| `DJANGO_DEBUG` | 로컬 개발은 `True` |
| `DJANGO_ALLOWED_HOSTS` | 허용 호스트. 기본 `localhost,127.0.0.1` |
| `MYSQL_DATABASE` | 개발 데이터베이스 이름 |
| `MYSQL_USER` / `MYSQL_PASSWORD` | 데이터베이스 접속 계정 |
| `MYSQL_HOST` / `MYSQL_PORT` | MySQL 주소 및 포트 |
| `MYSQL_TEST_DATABASE` | 개발 DB와 다른 테스트 전용 DB 이름. 기본 `test_nodeverse` |
| `ADMIN_REGISTRATION_CODE` | 관리자 가입 초대 코드. 비어 있으면 가입 불가 |

비밀 키와 초대 코드는 다음 명령으로 각각 생성할 수 있습니다.

```powershell
.\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(48))"
```

### 3. MySQL 준비

MySQL 관리 계정으로 개발 DB를 생성하고, `.env`에 지정한 사용자에게 해당 DB의 권한을 부여합니다.

```sql
CREATE DATABASE nodeverse CHARACTER SET utf8mb4;
```

테스트 실행 계정에는 별도 테스트 DB를 생성·삭제할 권한도 필요합니다. 개발 DB와 테스트 DB 이름은 반드시 다르게 설정합니다.

### 4. 마이그레이션 및 서버 실행

```powershell
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py runserver
```

1. `http://127.0.0.1:8000/staff/register/`에서 `.env`의 초대 코드로 관리자를 등록합니다.
2. `http://127.0.0.1:8000/staff/login/`에서 로그인합니다.
3. `http://127.0.0.1:8000/staff/`에서 분석 화면을 확인합니다.

관리자 로그인 계정과 분석 대상 `Player`는 분리되어 있습니다. 데모 데이터 생성 명령은 로그인 계정을 만들지 않습니다. Django 기본 `/admin/` 화면은 연결되어 있지 않습니다.

## 데모 데이터

`DJANGO_DEBUG=True`인 로컬 환경에서 실행합니다.

```powershell
# 대시보드 탐색용: 기본 36명, 문제 실행 504건
.\.venv\Scripts\python.exe manage.py seed_observatory

# 선택: 간단한 세션·이벤트 데이터
.\.venv\Scripts\python.exe manage.py seed_analytics_demo

# 선택: 문제·시도·연산으로 구조화된 학습 데이터
.\.venv\Scripts\python.exe manage.py seed_learning_demo
```

`seed_observatory --players 12 --visits 7`처럼 규모를 조정할 수 있습니다. 생성기는 기존 기록을 보존하며, 동일 식별자의 데이터를 중복 생성하지 않습니다. 데이터 필터에서 `데모 데이터`를 선택해 확인하세요. `seed_demo`는 `seed_analytics_demo`의 호환용 별칭입니다.

## 주요 화면 및 API

| 경로 | 기능 |
| --- | --- |
| `/staff/` | 종합·게임별·플레이어별 대시보드 |
| `/staff/players/` | 플레이어 목록 |
| `/staff/players/<UUID>/` | 플레이어 상세 |
| `/staff/events/` | 행동 이벤트 목록 |
| `/staff/guide/` | 분석 가이드 |
| `/staff/export/` | 필터에 해당하는 문제 실행 CSV |

인증 API는 `/api/auth/csrf`, `/api/auth/register`, `/api/auth/login`, `/api/auth/me`, `/api/auth/logout`입니다. 변경 요청에는 세션 쿠키와 CSRF 처리가 필요합니다.

관리자 전용 조회 API는 다음과 같습니다. API 경로에는 끝 슬래시가 없습니다.

| GET 경로 | 응답 내용 |
| --- | --- |
| `/api/admin/me` | 현재 관리자 |
| `/api/admin/summary` | 요약 및 학습 지표 |
| `/api/admin/visuals` | 차트 데이터 |
| `/api/admin/players` | 플레이어 목록 |
| `/api/admin/players/<UUID>` | 플레이어 상세 분석 |
| `/api/admin/events` | 행동 이벤트 목록 |

분석 API는 `start`, `end`, `source`, `topic`, `player_id`, `q`, `task_id`, `content_version` 등의 쿼리 필터를 지원합니다. 이벤트 목록에는 `event_type`을 사용할 수 있습니다.

## 데이터 구조

| 모델 | 역할 |
| --- | --- |
| `accounts.User` | 웹 관리자 인증 계정 |
| `Player` | 외부 ID와 실제·데모 출처를 가진 분석 대상 |
| `PlaySession` | 플레이어의 게임 세션 |
| `LearningTask` | 문제 ID·콘텐츠 버전별 학습 문제 |
| `TaskRun` | 한 번의 문제 실행과 실제 풀이·일시정지 시간 |
| `SolveAttempt` | 문제 실행 안의 개별 풀이 시도 |
| `BehaviorEvent` | 행동 순서, 연산·실패 원인, 전후 상태, 힌트 기록 |

세션별 이벤트 순서와 문제별 시도 번호에 유일성 제약이 있습니다. 구조화된 이벤트 기록·종료 처리는 `telemetry/recording.py`에서 관리합니다.

## 프로젝트 구조

```text
accounts/       관리자 계정, 인증, 가입 폼, 테스트
config/         Django 설정 및 URL
telemetry/      학습 데이터 모델, 기록, 집계, 차트, 조회, 테스트
templates/      관리자 인증 및 분석 화면
static/         스타일 및 JavaScript
docs/           규약, JSON 예시, SQL 참고 자료, 문서 생성 스크립트
output/         공유용 PDF, 이미지, 문서 ZIP
manage.py       Django 관리 명령 진입점
.env.example    환경 변수 예시 (비밀 값 없음)
```

## 문서

- [설치·실행 가이드](output/pdf/NODEVERSE_설치_실행_가이드.pdf)
- [데이터셋·대시보드 설계](output/pdf/NODEVERSE_데이터셋_대시보드_설계.pdf)
- [Unity 통신 규약](output/pdf/NODEVERSE_Unity_통신_규약.pdf)
- [팀 공유 아키텍처·데이터셋 정의서](output/pdf/NODEVERSE_팀공유_아키텍처_데이터셋_정의서.pdf)
- [팀 공유 이벤트 파이프라인 연동 규약서](output/pdf/NODEVERSE_팀공유_이벤트_파이프라인_연동규약서.pdf)
- [팀 공유 문서 상태 및 버전](docs/team_handoff/manifest.json)
- [기존 이벤트 스키마](docs/contracts/behavior-event.schema.json)
- [SQL 스키마 참고](docs/sql/schema_reference.sql) / [분석 쿼리](docs/sql/analysis_queries.sql)

설계 문서에는 향후 연동 제안도 포함됩니다. 실제 실행 경로와 DB 구조는 Django 코드 및 마이그레이션을 기준으로 확인합니다. 문서 생성 작업이 필요하면 `docs/requirements.txt`의 별도 의존성을 설치합니다.

## 점검 및 테스트

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py test accounts telemetry
```

기존 테스트는 관리자 인증·권한·CSRF, 분석 필터·집계, 데이터 제약, 이벤트 검증, 데모 생성의 중복 방지, 차트 및 CSV 접근 제어 등을 다룹니다. 전체 테스트는 전용 MySQL 테스트 DB를 생성·삭제합니다.

## Git 업로드

`.env`, 가상환경, Python 캐시, 임시 작업물은 `.gitignore`에서 제외합니다. `.env.example`, 소스 코드, 마이그레이션과 공유 문서는 포함합니다.

아직 Git 저장소가 없는 경우 프로젝트 루트에서 실행합니다. 원격 URL은 본인의 저장소 주소로 바꾸세요.

```powershell
git init
git branch -M main
git add .
git status
git diff --cached --stat
git commit -m "Initial commit: NODEVERSE admin analytics dashboard"
git remote add origin <YOUR_REPOSITORY_URL>
git push -u origin main
```

커밋 전에 스테이징 목록에 실제 비밀 값이나 개인 데이터가 없는지 확인하세요. 로컬 실행은 개발 서버 기준이며, 운영 배포 시 HTTPS와 운영용 서버·정적 파일 제공 설정이 별도로 필요합니다.
