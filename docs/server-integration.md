# 서버 파트 연동 안내 (로컬 실행 기준)

게임·파이프라인·서버 PC 담당자가 각자 설정할 내용입니다. 로컬(같은 네트워크) 실행을 먼저 맞추고, HTTPS와 외부 공개는 나중 단계에서 합니다.

## 전체 흐름

```text
게임 → 수집 API(/v2/events) → Kafka → Spark → Delta / MongoDB(서버 PC) → Django
게임 → Django(/api/game/auth/*) → MySQL(서버 PC)         회원가입·로그인·클라우드 세이브
게임 → Django(/api/game/manifest, /downloads/packs/*)     업데이트 확인·리소스 팩
```

Django가 받는 요청은 다음 두 가지뿐입니다.

- 게임 클라이언트의 공개 요청: 회원가입·로그인, 매니페스트, 팩 파일
- 서버 간 요청: `/api/game/records`, `/api/game/player-login` (`GAME_SERVER_API_KEY`)

게임의 학습 이벤트는 파이프라인 수집 API로만 들어옵니다. 게임과 포털에는 DB 비밀번호나 `GAME_SERVER_API_KEY`를 넣지 않습니다.

| 역할 | 위치 |
| --- | --- |
| Django (대시보드, 게임 로그인 API, 매니페스트) | 192.168.0.29:8000 |
| MySQL `nodeverse` (회원, 로그인 기록, 릴리스·팩) | 192.168.0.167:3306 |
| MongoDB `nodeverse_logs` (게임 로그, `rt_*`) | 192.168.0.167:27017 |
| 수집 API, Kafka, Spark | 파이프라인 PC:8000 |

---

## 1. 서버 PC (192.168.0.167) 담당

1. **MongoDB를 네트워크에서 접속 가능하게 설정합니다.** 현재 Django PC에서 27017 포트에 연결되지 않습니다.
   - `mongod.cfg`의 `net.bindIp`에 `0.0.0.0` 또는 서버 PC IP를 추가하고 MongoDB를 재시작합니다.
   - Windows 방화벽의 인바운드 규칙에서 27017을 엽니다. 허용 대상은 **Django PC(.29)와 파이프라인 PC만**입니다.
2. **MongoDB 인증을 켭니다.** `output/server_setup/02_mongodb_accounts.js`로 계정을 만든 뒤 `security.authorization: enabled`를 적용합니다.
   - 파이프라인 Spark용 계정: `nodeverse_logs`의 `rt_*`에 쓰기 권한
   - Django용 계정: `nodeverse_dashboard_reader` (읽기 전용)
3. **MySQL:** 3306은 Django PC(.29)에만 엽니다. 현재 Django 계정으로 연결은 됩니다. `nodeverse_dev` 계정에는 테이블 생성·변경 권한이 이미 있습니다.

## 2. 파이프라인 PC 담당

1. **Spark의 MongoDB 출력 주소를 서버 PC로 바꿉니다.** 지금은 Docker 안의 `mongodb://127.0.0.1:27017`에 씁니다.
   - 변경할 주소: `mongodb://<spark계정>:<비밀번호>@192.168.0.167:27017/nodeverse_logs?authSource=nodeverse_logs`
   - 컬렉션 이름과 `_id` 규칙(`rt_minigame_1m`, `rt_alerts`, `rt_summary`, `rt_updates`, `rt_versions`)은 공통 계약 그대로입니다.
   - `window_start`, `updated_at`은 BSON Date(UTC)로 넣어 주세요. Django가 이 필드로 범위를 조회합니다.
2. **수집 API를 다른 PC에서 받을 수 있게 엽니다.** `COLLECTOR_BIND=0.0.0.0`으로 설정하고 방화벽 8000을 엽니다. 결과서의 "알려진 제약" 항목입니다.
3. 지연과 부하 시험은 실제 PC에서 다시 측정합니다(결과서 12장). 측정하는 동안 Django의 `/staff/live/`를 켜 두고 같이 확인합니다.

## 3. 게임 담당

1. **주소 두 개를 설정합니다.**
   - 이벤트: `http://<파이프라인PC>:8000/v2/events` (지금과 같음)
   - 매니페스트: `http://192.168.0.29:8000/api/game/manifest?channel=windows-stable`
   - 로컬 실행 동안은 HTTP를 씁니다. 외부 공개 단계에서 HTTPS 주소로 바꿉니다.
2. **회원가입·로그인·클라우드 세이브는 이미 구현된 `/api/game/auth/*`를 그대로 씁니다** (커밋 5b79ea4). 요청·응답 형식은 바뀌지 않았습니다.

   | API | 보내는 값 | 성공 응답 |
   | --- | --- | --- |
   | `POST /api/game/auth/register` | `username`, `password`, `recovery_key`(선택) | 201, `username`, `player_id`, `save_data` |
   | `POST /api/game/auth/login` | `username`, `password` | 200, `username`, `player_id`, `save_data` |
   | `POST /api/game/auth/find-id` | `recovery_key` | 200, `usernames` |
   | `POST /api/game/auth/reset-password` | `username`, `recovery_key`, `new_password` | 200 |
   | `POST /api/game/auth/save` | `username`, `save_data` | 200 |

   서버 쪽에서 추가된 동작:
   - **기록:** 가입·로그인·아이디 찾기·비밀번호 재설정 시도가 모두 `game_login_history`에 남습니다(성공·실패, 실패 사유, IP). 대시보드 `/staff/members/`에 표시됩니다.
   - **선택 필드:** 요청에 `install_id`, `build_version`, `content_version`을 같이 보내면 기록에 함께 남습니다. 보내지 않아도 동작은 같습니다.
   - **요청 제한 (429):** IP당 1분에 30회, 아이디당 10분에 로그인·재설정 실패 10회를 넘으면 `{"success": false, "message": ...}`와 429를 돌려줍니다. 게임은 `message`를 그대로 보여 주면 됩니다.
   - **비밀번호 재설정:** 복구 키(`recovery_key`)가 등록된 계정만, 그 키가 맞을 때만 바뀝니다. 복구 키 없이 가입한 계정은 403입니다. 예전에는 복구 키가 없는 계정을 누구나 재설정할 수 있었습니다.
3. **진행률은 클라우드 세이브에서 읽습니다.** 대시보드는 `save_data.minigame_cleared`의 키를 24개 미니게임 실행 ID(`ST01`~`ST10`, `DS09`, `DS10`, `ALG01`~`ALG04`, `SQL01`~`SQL04`, `DATA01`~`DATA04`, 대소문자 무관)와 맞춰 봅니다.
   - 키를 실행 ID로 저장하면 영역별 카드에 표시됩니다. 값은 별 개수(0~3)나 `true`입니다.
   - 다른 이름으로 저장한 키는 회원 상세의 "다른 이름으로 저장된 클리어 기록"에 따로 나옵니다.
4. 학습 이벤트의 `player_id`는 지금처럼 설치 ID를 그대로 씁니다. 공통 계약은 바꾸지 않습니다.
5. **매니페스트 동작 확인:** 릴리스가 없으면 404를 돌려주고, 게임은 지금처럼 offline으로 처리하면 됩니다. 팩 파일은 매니페스트의 `url`에서 받습니다. 해시는 서버가 직접 계산합니다.
6. 팩을 만들면(`tools/make_pack.ps1`) 서버 담당에게 `.pck` 파일과 필요한 최소 빌드를 전달합니다. 등록은 서버 담당이 `/staff/releases/`에서 합니다.

**남은 보안 과제 (게임·서버 같이 정할 것):** `/save`는 아이디만 알면 누구나 그 계정의 세이브를 덮어쓸 수 있습니다. 로그인 때 토큰을 발급하고 `/save`에서 확인하는 방식으로 바꿔야 합니다. 비밀번호 최소 3자도 외부 공개 전에는 8자 이상으로 올립니다.

## 4. 서버(Django) 담당

1. `.env`에서 `MONGODB_URI`를 서버 PC의 읽기 전용 계정 주소로 바꿉니다. 서버 PC 담당 1~2번이 끝난 뒤에 합니다.
2. **새 MySQL 테이블을 만듭니다.**
   ```powershell
   .\.venv\Scripts\python.exe manage.py migrate
   ```
   추가되는 테이블은 `game_accounts`(게임 팀), `game_login_history`, `game_releases`, `game_content_packs`입니다. 예전 시험용 `game_member_credentials`는 삭제됩니다. 공유 DB이므로 팀에 알리고 실행합니다.
3. **다른 PC에서 접속되게 실행합니다.**
   ```powershell
   .\.venv\Scripts\python.exe manage.py runserver 0.0.0.0:8000
   ```
   - Windows 방화벽에서 8000 포트를 같은 네트워크에만 엽니다.
   - `.env`의 `DJANGO_ALLOWED_HOSTS`에 `192.168.0.29`가 있어야 합니다(현재 있음).
   - 이 PC의 IP가 바뀌지 않도록 공유기에서 고정합니다.
4. 파이프라인 데이터가 들어오기 전에는 목업으로 화면을 확인합니다.
   ```powershell
   .\.venv\Scripts\python.exe manage.py seed_rt
   ```
   실데이터가 들어오면 목업만 지웁니다. Spark가 쓴 문서는 지우지 않습니다.
   ```powershell
   .\.venv\Scripts\python.exe manage.py seed_rt --clear
   ```
   목업은 읽기 전용 계정으로는 넣을 수 없으니 쓰기 권한이 있는 환경에서 실행합니다.
5. 첫 릴리스를 `/staff/releases/`에서 등록합니다. 예: `0.3.0` / 최소 `0.3.0`.

## 화면과 API

| 경로 | 내용 |
| --- | --- |
| `/staff/live/` | 실시간 학습 현황: 최근 1분 이벤트, 5분 활성 세션, 미니게임별 성공률 추이, 영역별 시도, 실패 급증 경고. 3초마다 갱신하고, 30초 넘게 갱신이 없으면 "수집 지연"을 표시 |
| `/staff/live/?tab=updates` | 업데이트 진행: 보급률, 최소 빌드 미만 설치, 다운로드 추이, 실패 사유, 안내 반응. 최근 15분 실패율이 0.2 이상이면 "팩 비활성화 검토" 표시 |
| `/staff/members/` | 게임 회원(`game_accounts`): 가입·로그인·실패 기록, 일별 로그인, 클라우드 세이브 기준 미니게임 클리어·별·점수 |
| `/staff/releases/` | 릴리스·팩 등록과 켜기/끄기 (파일은 삭제하지 않음) |
| `/download/` | 공개 다운로드 페이지. 매니페스트의 `download_page` |
| `GET /api/admin/live/{summary,minigames,alerts,updates}?minutes=1~180` | 관리자 전용, no-store |
