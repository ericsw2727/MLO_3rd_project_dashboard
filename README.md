# NODEVERSE

스택·큐·트리 학습 게임의 플레이 기록을 분석하는 **Django 기반 관리자 대시보드**입니다. 플레이어의 문제 풀이, 재시도, 연산 실패, 힌트 사용과 풀이 시간을 조회하고 비교합니다.

## 구현 현황

- 공개 게임 소개·브라우저 체험 홈페이지(`/`)와 관리자 로그인·대시보드(`/staff/`) 연결
- 관리자 초대 코드 기반 가입, 로그인·로그아웃, 세션 인증 및 CSRF 보호
- 전체 종합 / 게임별 / 플레이어별 분석 화면
- 기간, 실제·데모 데이터, 자료구조, 플레이어, 문제 ID, 콘텐츠 버전 필터
- 플레이어 목록·상세, 행동 이벤트 조회 및 페이지네이션
- 문제 해결·포기·재시도·힌트·실패 원인·풀이 시간 분석과 차트
- 문제 실행 기록 CSV 내보내기
- 관리자 전용 조회 API와 합성 데모 데이터 생성 명령
- 게임 서버의 로그인 완료 회원 정보 수신 및 실제 플레이어 연결 ([연동 규약](docs/game-login-integration.md))
- 데이터 모델, 이벤트 규약, SQL 참고 자료 및 팀 공유 문서

**현재 실행 애플리케이션은 Django + MySQL + MongoDB 구성입니다.** 회원·관리자 정보는 MySQL, 플레이 세션·문제 정의·문제 실행·풀이 시도·행동 이벤트는 MongoDB에 저장합니다. 게임 서버 전용 수집 API는 [MongoDB 연동 규약](docs/mongodb-integration.md)을 참고하세요. Godot 클라이언트와 파이프라인 진단 연동은 별도 구현 범위입니다. `docs/team_handoff`의 규약 3.0은 팀 검토용 제안입니다.

### 게임 홈페이지와 관리자 연결

서버 실행 후 `http://127.0.0.1:8000/`에서 제공받은 NODEVERSE 소개·체험 페이지를 볼 수 있습니다. 상단의 **관리자 로그인** 또는 하단의 **관리자 전용 포털**을 누르면 기존 Django 관리자 인증 화면으로 이동합니다. 로그인한 관리자는 `/staff/`에서 실제 DB 기반 분석을 조회하며, 사이드바의 **게임 홈페이지**로 돌아갈 수 있습니다.

팀원 웹사이트의 원본은 `website/`입니다. 원본을 수정한 뒤 아래 명령으로 Django 템플릿과 스크립트를 갱신합니다.

```powershell
.\.venv\Scripts\python.exe docs/sync_website.py
```

`templates/portal/index.html`과 `static/portal/`의 JS·CSS는 생성 결과입니다. 이미지·새 소개 영상은 `website/assets/`에서 정적 파일로 제공하므로 중복 보관하지 않습니다. 상단 관리자 링크와 기존 `dashboard.html`은 Django의 `/staff/`로 연결되며, 브라우저 암호 검사나 샘플 관리자 데이터는 사용하지 않습니다.

다운로드 주소는 `website/config.js`의 `gameDownloadUrl`에서 설정합니다. 코봇 채팅 UI와 내장 게임 안내는 유지하지만, 외부 AI 서비스 호출은 브라우저 비밀키 노출을 막기 위해 비활성화했습니다. 실시간 AI를 사용하려면 서버 측 인증·호출 경로를 별도 구현해야 합니다. API 키를 공개 JS에 넣거나 뒤집기·인코딩으로 감춰 배포하지 않습니다. 공개 체험판의 행동을 DB로 전송하는 기능은 별도 연결 대상입니다.

이 구성은 로컬 Django 서버에 통합한 결과입니다. 기존 외부 호스팅 페이지는 변경하지 않았습니다. 운영 배포 시에는 Django와 정적 파일(`/static/`)을 함께 제공해야 하며, 파일을 더블클릭하거나 정적 호스팅에 HTML만 올려서는 관리자 서버가 실행되지 않습니다.

## 기술 구성

| 구분 | 사용 기술 |
| --- | --- |
| 서버 | Python, Django 5.2 |
| 데이터베이스 | MySQL (회원·관리자), MongoDB + PyMongo (학습 기록) |
| 화면 | Django Templates, CSS, JavaScript |
| 환경 설정 | python-dotenv |
| 문서 생성 | ReportLab (별도 의존성) |

정확한 애플리케이션 의존성 버전은 [requirements.txt](requirements.txt)를 참고하세요.

## 로컬 설치 및 실행

아래 명령은 Windows PowerShell 기준입니다. Python, MySQL 및 MongoDB 서버가 필요하며, `mysqlclient` 설치 시 환경에 따라 빌드 도구 또는 MySQL 클라이언트 개발 라이브러리가 필요할 수 있습니다.

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
| `GAME_SERVER_API_KEY` | 게임 서버 전용 회원·로그 API 인증 키 |
| `MONGODB_URI` | 필수. MongoDB 접속 URI |
| `MONGODB_DATABASE` | 로그 DB 이름. 기본 `nodeverse_logs` |

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

먼저 [MongoDB 준비 방법](docs/mongodb-setup.md)에 따라 접속 정보를 설정합니다. `0005` 마이그레이션은 기존 MySQL 로그를 MongoDB에 복사·검증한 뒤 MySQL 로그 테이블 5개를 제거합니다. MongoDB 접속 실패나 기존 문서 충돌 시 테이블 삭제 전에 중단됩니다. 작업 중에는 앱을 중지하고 DB를 백업하세요. 자동 역방향 마이그레이션은 데이터 유실 방지를 위해 차단됩니다.

```powershell
.\.venv\Scripts\python.exe manage.py check_mongodb
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py runserver
```

1. `http://127.0.0.1:8000/staff/register/`에서 `.env`의 초대 코드로 관리자를 등록합니다.
2. `http://127.0.0.1:8000/staff/login/`에서 로그인합니다.
3. `http://127.0.0.1:8000/staff/`에서 분석 화면을 확인합니다.

관리자 로그인 계정과 분석 대상 `Player`는 분리되어 있습니다. 데모 데이터 생성 명령은 로그인 계정을 만들지 않습니다. Django 기본 `/admin/` 화면은 연결되어 있지 않습니다.

로컬 실행 확인 시 로그인 화면의 **관리자 테스트 로그인** 버튼을 사용할 수 있습니다. `DEBUG=True`이고 localhost/127.0.0.1에서 직접 접속할 때만 표시·동작하며, CSRF가 적용된 POST 요청으로 테스트 관리자 계정을 만들거나 재사용합니다. 테스트 계정에는 사용 가능한 비밀번호와 superuser 권한을 부여하지 않으며 로그인은 1시간 유지됩니다. 게임 회원·데모 로그는 만들지 않습니다. `DEBUG=False`에서는 테스트 버튼과 기존 테스트 계정 세션 모두 비활성화됩니다.

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

실제 저장 이름은 [데이터 이름 안내](docs/database-names.md)를 참고하세요. 회원은 MySQL, 학습 기록과 대시보드 지표는 MongoDB를 사용합니다. [MongoDB 준비 방법](docs/mongodb-setup.md)과 [수집 API 규약](docs/mongodb-integration.md)을 참고하세요.

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

테스트는 관리자 인증·권한·CSRF, 분석 필터·집계, 이벤트 검증, 중복 방지, 차트·CSV 및 게임 서버 수집을 다룹니다. 전용 SQL 테스트 DB와 무작위 이름의 MongoDB 테스트 DB를 생성·삭제합니다. 개발 로그 DB에는 테스트 데이터를 쓰지 않습니다.

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
