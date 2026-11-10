# MongoDB 준비 방법

MySQL에 회원·관리자 정보, MongoDB에 플레이 기록을 저장합니다. 환경 변수 설정 후 `check_mongodb`와 `migrate`를 실행합니다. [이전·수집 API 규약](mongodb-integration.md)을 참고하세요.

## 방법 1: MongoDB Atlas

서버에 직접 설치하지 않고 준비할 수 있습니다.

1. [MongoDB Atlas](https://www.mongodb.com/atlas)에 가입하고 프로젝트와 클러스터를 생성합니다. 학습용이면 생성 화면의 Free 옵션을 확인합니다.
2. Database Access에서 DB 접속 사용자를 만듭니다. Atlas 로그인 계정과 DB 접속 계정은 다릅니다. 앱 계정에는 `nodeverse_logs` DB의 `readWrite` 권한을 부여합니다.
3. Network Access에 Django 서버가 외부로 접속할 때 사용하는 공인 IP를 등록합니다. 로컬 개발 PC에서 접속한다면 그 PC의 공인 IP도 필요합니다. `192.168.*` 사설 IP는 Atlas 접속 허용 IP가 아닙니다.
4. 클러스터의 Connect → Drivers → Python에서 연결 문자열을 복사합니다.
5. 실제 사용자·비밀번호를 넣고 `.env`에 저장합니다. 비밀번호에 특수 문자가 있으면 URI 퍼센트 인코딩이 필요합니다. 연결 문자열을 채팅이나 Git에 올리지 않습니다.

```dotenv
MONGODB_URI=mongodb+srv://USER:ENCODED_PASSWORD@YOUR_CLUSTER.mongodb.net/?retryWrites=true&w=majority
MONGODB_DATABASE=nodeverse_logs
```

Compass에서도 같은 URI로 접속할 수 있습니다. 접속 성공과 DB에 읽기·쓰기할 권한은 별개이므로 앱 계정 권한도 확인합니다.

공식 안내: [Atlas 연결](https://www.mongodb.com/docs/atlas/connect-to-database-deployment/), [접속 설정](https://www.mongodb.com/docs/atlas/security/quick-start/).

## 방법 2: 기존 Windows DB 서버 PC에 설치

1. 서버 PC에 [MongoDB Community Server](https://www.mongodb.com/docs/v8.0/tutorial/install-mongodb-on-windows/)를 설치합니다. 설치 시 Windows Service 옵션을 선택합니다.
2. MongoDB Compass를 설치합니다. 명령행 작업용 `mongosh`도 별도 설치 여부를 확인합니다. Compass는 서버 자체가 아니라 DB 관리 도구입니다.
3. 서버 PC의 `localhost:27017`에서 먼저 접속을 확인합니다. 아직 외부 네트워크에 공개하지 않은 상태에서 관리자와 앱 사용자를 만듭니다.
4. 서버 PC의 `mongosh`에서 아래 예시를 실행합니다. 비밀번호는 프롬프트에 입력합니다.

```javascript
use admin
db.createUser({user: "nodeverse_db_admin", pwd: passwordPrompt(), roles: ["userAdminAnyDatabase"]})
use nodeverse_logs
db.createUser({user: "nodeverse_app", pwd: passwordPrompt(), roles: [{role: "readWrite", db: "nodeverse_logs"}]})
```

5. 설치 디렉터리의 `bin/mongod.cfg`에서 기존 설정에 아래 항목을 병합합니다. `192.168.0.167`은 현재 MySQL 서버 주소 예시이며, MongoDB를 설치한 PC의 실제 주소를 사용합니다.

```yaml
net:
  port: 27017
  bindIp: 127.0.0.1,192.168.0.167
security:
  authorization: enabled
```

6. Windows 서비스에서 MongoDB를 재시작합니다. 방화벽 TCP 27017은 Django 서버 등 필요한 PC의 사설 IP에만 허용합니다. 인터넷 포트포워딩은 하지 않습니다.
7. Django PC의 `.env`에 설정합니다. 비밀번호는 URI에 맞게 인코딩합니다.

```dotenv
MONGODB_URI=mongodb://nodeverse_app:ENCODED_PASSWORD@192.168.0.167:27017/nodeverse_logs?authSource=nodeverse_logs
MONGODB_DATABASE=nodeverse_logs
```

이 방식은 같은 신뢰할 수 있는 사설망 기준입니다. 외부 네트워크를 통과한다면 TLS/VPN 등 별도 연결 구성이 필요합니다.

## 연결 점검

서버 설치 후 Compass로 먼저 연결합니다. PyMongo는 필수 의존성에 포함되어 있습니다. 프로젝트 루트에서 다음 명령으로 연결을 점검할 수 있습니다.

```powershell
.\.venv\Scripts\python.exe -m pip install pymongo
@'
import os
from dotenv import load_dotenv
from pymongo import MongoClient
load_dotenv()
with MongoClient(os.environ['MONGODB_URI'], serverSelectionTimeoutMS=5000) as client:
    print(client.admin.command('ping'))
'@ | .\.venv\Scripts\python.exe -
```

`ping`은 서버 접속만 확인합니다. 앱의 인덱스 생성·조회는 `python manage.py check_mongodb`로 확인합니다. 공식 예제: [PyMongo 시작하기](https://www.mongodb.com/docs/languages/python/pymongo-driver/current/get-started/).

## 이후 저장 구조

MySQL `game_members.member_id`(Django 필드 id)를 MongoDB `game_sessions.player_id`에 UUID 문자열로 연결합니다. 게임 서버 원본 회원 ID가 아니라 회원 수신 응답의 `player_id`를 사용합니다. MongoDB와 MySQL 사이에는 DB 외래 키가 없으므로 서버에서 회원 존재 여부를 검증합니다.

MongoDB 컬렉션은 `game_sessions`, `game_problems`, `problem_runs`, `solution_attempts`, `gameplay_events`입니다. `game_problems`는 문제 정의입니다. 0005 마이그레이션이 기존 기록을 복사·검증한 뒤 MySQL 로그 테이블을 제거합니다.
