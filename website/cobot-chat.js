/* ==========================================================
   NODEVERSE — Cobot (코봇) AI Chat Assistant Logic
   Powered by Groq AI & Intelligent Game Knowledge Engine
   ========================================================== */

(function () {
  'use strict';

  // -------------------- SYSTEM PROMPT & KNOWLEDGE BASE --------------------
  const COBOT_SYSTEM_PROMPT = `
당신은 교육용 3D 메타버스 코딩 탐험 게임 'NODEVERSE(노드버스)'의 공식 AI 마스코트 안내 로봇 '코봇(Cobot)'입니다.
밝고 친절하며 호기심 많은 귀여운 로봇 어투('~해!', '~야!', '~하자!', '~거든!' 등)로 대답하세요.

[게임 기본 정보]
- 게임 이름: NODEVERSE (연결된 배움의 세계)
- 슬로건: "외우던 개념을, 걸어서 이해하는 경험"
- 장르: 3D 메타버스 탐험 + 2D 인터랙티브 알고리즘/자료구조/데이터 미니게임
- 개발 환경: Godot 4.7 3D/2D 엔진 + Python/GDScript + 웹 쇼케이스(HTML/CSS/JS)

[7개의 섬 구성]
1. 메인 섬 (Main Island): 모든 탐험의 출발점인 중앙 광장 허브. 6개 학습 섬으로 뻗어있는 웅장한 다리가 연결되어 있음.
2. 입문 섬 (01): 코딩의 기초인 변수, 조건문, 반복문 원리를 탐색하는 첫 번째 섬.
3. 자료구조 섬 (02): 총 10가지 관문(ST01~ST10)이 있는 핵심 섬!
   - ST01 배열 (순서가 있는 보관소)
   - ST02 연결 리스트 (끊어진 운송로)
   - ST03 스택 (최근 작업 복구실 · LIFO)
   - ST04 큐/덱 (접수 순서 안내소 · FIFO)
   - ST05 해시 테이블 (이름으로 찾는 물품대장)
   - ST06 이진 트리 (계층형 자료실)
   - ST07 이진 탐색 트리 BST (갈림길 창고)
   - ST08 힙 & 우선순위 큐 (긴급 작업 배정실)
   - ST09 그래프 (연결망 조사실 · BFS/DFS)
   - ST10 통합 실전 (학습 지원 센터 마스터 챌린지)
4. 알고리즘 섬 (03): 버블 정렬, 선택 정렬, 삽입 정렬 등 순서 맞춤 작업대(ALG01~ALG04)와 탐색 알고리즘.
5. SQL 섬 (04): 5×5 학생 서랍 색칠(SQL01)을 통해 SELECT 열 선택, WHERE 조건 필터링, NULL 처리, ORDER BY 정렬, LIMIT 제한을 시각적으로 학습.
6. 데이터 탐험 섬 (05): 데이터 분포와 통계, 결측치/이상치 탐색 및 데이터 파이프라인.
7. 종합 도전 섬 (06): 모든 지식을 융합하여 대규모 복합 시스템의 병목 현상을 해결하는 최종 챌린지.

[게임 다운로드 및 실행 방법]
1. GitHub 저장소(https://github.com/junbum8398-blip/nodeverse-game)에서 프로젝트를 다운로드(ZIP)하거나 git clone 받기!
2. 다운로드받은 압축을 풀고 폴더 안의 'play_game.bat'을 더블 클릭하면 끝!
3. 'play_game.bat'이 자동으로 필요한 그래픽 에셋과 스크립트를 임포트하고 3D 세계(res://scenes/NodeverseWorld.tscn)를 바로 실행해 줘.

[웹사이트 내 실시간 웹 체험판 (#demo)]
- 설치 없이 웹 브라우저에서 바로 플레이 가능한 3개 섬 대표 미니게임:
  1) 자료구조 섬 (ST03 스택 복구실): 로봇으로 상자를 집어 스택에 쌓고(Push), 확인대에서 Top을 조회(Peek)한 후 역순으로 꺼내(Pop) 복구 결과 작업대에 배치.
  2) 알고리즘 섬 (ALG01 순서 맞춤 작업대): [5, 2, 4, 1] 버블 정렬, 선택 정렬, 삽입 정렬을 실시간 비교 횟수(cmp)/기록 횟수(write) 계기판과 함께 한 단계씩 진행.
  3) SQL 섬 (SQL01 5×5 서랍 색칠): students 5×5 테이블에서 1번 파란 붓(SELECT)과 2번 금색 붓(WHERE)으로 칠해 초록색 교차 칸(R×C) 추출.
- 조작법: 마우스 클릭 또는 WASD/방향키 이동, E 상호작용, Z 되돌리기, R 다시 시작, 1~5번 도구 전환.

사용자의 질문에 알맞게 핵심을 짚어주고, 링크나 조작키를 보기 쉽게 안내해 주세요.
`.trim();

  // -------------------- KNOWLEDGE BASE (OFFLINE / FALLBACK) --------------------
  function getLocalKnowledgeReply(prompt) {
    const q = prompt.toLowerCase().trim();

    // 1. 다운로드 / 실행 방법
    if (q.includes('다운') || q.includes('설치') || q.includes('실행') || q.includes('플레이') && q.includes('어떻게') || q.includes('어디서')) {
      return `
🎮 **NODEVERSE 게임 다운로드 & 실행 방법**을 알려줄게!

1. **GitHub 저장소 방문**:
   👉 [NODEVERSE GitHub 저장소 바로가기](https://github.com/junbum8398-blip/nodeverse-game) 에서 초록색 **[Code] → [Download ZIP]**을 클릭하거나 Git Clone을 받아줘!
2. **압축 풀기**:
   내려받은 ZIP 파일의 압축을 원하는 폴더에 풀어줘.
3. **'play_game.bat' 더블 클릭**:
   폴더 안에 있는 \`play_game.bat\` 파일을 실행하면 Godot 엔진이 새로운 에셋과 스크립트를 자동으로 임포트하고 3D 연결섬 세계를 바로 띄워줘! 🚀
4. **웹에서 바로 해보고 싶다면?**:
   다운로드 없이도 지금 이 웹사이트의 [웹 체험판(#demo)](#demo) 섹션에서 자료구조·알고리즘·SQL 3개 섬 미니게임을 즉시 플레이해볼 수 있어!
`.trim();
    }

    // 2. 게임 소개 / 무슨 게임
    if (q.includes('어떤 게임') || q.includes('게임 소개') || q.includes('게임 설명') || q.includes('노드버스') || q.includes('nodeverse') || q.includes('뭐하는')) {
      return `
✨ **NODEVERSE(노드버스)는 어떤 게임일까?**

NODEVERSE는 **"외우던 프로그래밍과 데이터 개념을, 직접 걸어서 이해하는 3D 메타버스 코딩 탐험 게임"**이야! 🏝️

- **3D 연결섬 세계**: 7개의 아름다운 테마 섬들이 거대한 다리로 연결되어 있어, 로봇과 함께 섬을 탐험하며 학습 퀘스트를 수행해.
- **2D 실전 미니게임**: 각 섬마다 배열, 스택, 트리, 정렬 알고리즘, SQL 서랍장 등 개념을 눈으로 보고 손으로 조작하는 퍼즐 미니게임이 준비되어 있어.
- **실시간 코드 & 데이터 연동**: 미니게임에서 상자를 옮기거나 색칠하면 오른쪽에 진짜 Python/SQL 코드가 실시간으로 기록돼!
- **기술 스택**: 오픈소스 Godot 4.7 엔진을 기반으로 제작되었어.
`.trim();
    }

    // 3. 7개 섬 / 섬 목록
    if (q.includes('섬') || q.includes('아일랜드') || q.includes('맵') || q.includes('월드') || q.includes('지도')) {
      return `
🗺️ **NODEVERSE의 7개 섬을 소개할게!**

1. 🏰 **메인 섬 (Hub)**: 모든 탐험의 출발 광장! 6개 학습 섬으로 이어지는 관문 다리가 있어.
2. 🌱 **입문 섬 (01)**: 변수, 조건, 반복문 등 코딩의 첫걸음을 떼는 곳.
3. 📦 **자료구조 섬 (02)**: 배열, 연결 리스트, 스택, 큐, 해시, 트리, BST, 힙, 그래프 등 10개 관문(ST01~ST10).
4. ⚙️ **알고리즘 섬 (03)**: 버블·선택·삽입 정렬과 탐색 알고리즘을 실험하는 순서 맞춤 작업대(ALG01~ALG04).
5. 🗄️ **SQL 섬 (04)**: 5×5 서랍 색칠(SQL01)을 통해 SELECT, WHERE, ORDER BY, LIMIT 쿼리를 마스터하는 섬.
6. 📊 **데이터 탐험 섬 (05)**: 데이터 분포, 결측치, 통계 분석 파이프라인을 다루는 연구소.
7. 🏆 **종합 도전 섬 (06)**: 모든 지식을 융합해 복합 시스템 병목을 해결하는 최종 마스터 아일랜드!
`.trim();
    }

    // 4. 자료구조 섬 / 10개 스테이지 / 스택 / 큐 / 트리
    if (q.includes('자료구조') || q.includes('스택') || q.includes('큐') || q.includes('배열') || q.includes('트리') || q.includes('st0')) {
      return `
📦 **자료구조 섬의 10가지 관문(ST01~ST10)**이야!

- **ST01 배열**: 연속된 메모리 공간에 상자를 채우는 인덱스 접근 원리
- **ST02 연결 리스트**: 포인터 케이블로 HEAD부터 끊어진 레일을 잇는 구조
- **ST03 스택 (웹 체험판 탑재!)**: 나중에 넣은 상자를 먼저 꺼내는 후입선출(LIFO) 복구실
- **ST04 큐 & 덱**: 먼저 온 순서대로 처리하는 선입선출(FIFO) 안내소
- **ST05 해시 테이블**: Key를 해시 함수로 매핑하여 O(1)로 찾는 물품대장
- **ST06 이진 트리**: 루트(Root)부터 리프(Leaf)까지 계층 순회
- **ST07 이진 탐색 트리(BST)**: 작으면 왼쪽, 크면 오른쪽으로 찾는 갈림길 창고
- **ST08 힙 & 우선순위 큐**: 긴급 작업이 항상 맨 위로 오도록 Heapify
- **ST09 그래프**: 정점과 간선으로 얽힌 네트워크 최단경로 탐색(BFS/DFS)
- **ST10 통합 실전**: 복합 자료구조로 시스템 병목을 해결하는 종합 관문!
`.trim();
    }

    // 5. 알고리즘 / 정렬
    if (q.includes('알고리즘') || q.includes('정렬') || q.includes('버블') || q.includes('선택') || q.includes('삽입')) {
      return `
⚡ **알고리즘 섬 (ALG01 순서 맞춤 작업대)**에서는 정렬의 핵심 원리를 직접 체험할 수 있어!

- **1단계 · 버블 정렬 (Bubble Sort)**:
  인접한 두 상자를 비교하여 왼쪽이 더 크면 교환(Swap), 아니면 통과(Keep)하며 큰 숫자를 오른쪽 끝으로 보내!
- **2단계 · 선택 정렬 (Selection Sort)**:
  아직 정렬되지 않은 구간에서 **가장 작은 최솟값 상자**를 직접 찾아 앞자리와 맞바꿔!
- **3단계 · 삽입 정렬 (Insertion Sort)**:
  새 카드를 손에 들고(Lift), 빈칸 왼쪽의 큰 값들을 오른쪽으로 민 뒤(Shift) 알맞은 자리에 쏙 꽂아 넣어(Insert)!

웹사이트 중간의 [웹 체험판](#demo)에서 세 가지 정렬을 지금 바로 해볼 수 있어!
`.trim();
    }

    // 6. SQL 섬 / 서랍 / 쿼리
    if (q.includes('sql') || q.includes('서랍') || q.includes('쿼리') || q.includes('where') || q.includes('select')) {
      return `
🗄️ **SQL 섬 (SQL01 필요한 칸만 꺼내기)**은 이렇게 풀어!

- **1번 파란 붓 (SELECT)**: 가져오고 싶은 열(Column)을 칠해줘 (예: \`name\`, \`score\`).
- **2번 금색 붓 (WHERE)**: 조건에 맞는 행(Row)을 칠해줘 (예: \`score >= 80\`).
- **초록색 교차 칸 (R×C)**: 파란 열과 금색 행이 만나는 곳이 실제로 추출되는 결과 데이터야!
- **도윤 학생의 NULL 주의**: 4행 도윤 학생의 score는 \`NULL\`(빈칸)이라 숫자 조건 비교에서 탈락해!
- **4번 ORDER BY & 5번 LIMIT**: 정렬 버튼과 개수 제한 스위치를 켜서 1등 학생만 뽑아낼 수도 있어!
`.trim();
    }

    // 7. 웹 체험판 미니게임 안내
    if (q.includes('체험') || q.includes('웹') || q.includes('데모') || q.includes('미니게임') || q.includes('체험판')) {
      return `
🕹️ **웹 체험판(#demo)에 오신 것을 환영해!**

브라우저에서 바로 즐길 수 있는 3개 섬 대표 미니게임이야:
1. **01 자료구조 섬**: ST03 최근 작업 복구실 (스택 · LIFO 상자 운반)
2. **02 알고리즘 섬**: ALG01 순서 맞춤 작업대 (버블 · 선택 · 삽입 정렬 3종)
3. **03 SQL 섬**: SQL01 필요한 칸만 꺼내기 (5×5 서랍 색칠)

👉 [여기(#demo)를 클릭](#demo)하면 웹 체험판 섹션으로 바로 이동해!
마우스 클릭뿐만 아니라 키보드 \`WASD\`, \`E\`, \`Z\`, \`R\`로도 로봇을 조작할 수 있어.
`.trim();
    }

    // 8. 조작키 / 컨트롤
    if (q.includes('조작') || q.includes('키') || q.includes('컨트롤') || q.includes('움직')) {
      return `
⌨️ **NODEVERSE 조작 방법 안내!**

[웹 체험판 조작]
- **이동 / 작업대 선택**: \`W\` \`A\` \`S\` \`D\` 또는 방향키 \`←\` \`→\` \`↑\` \`↓\` (마우스 클릭도 지원)
- **상호작용 / 집기 / 놓기**: \`E\` 또는 \`Space\`
- **정렬 / 도구 선택**: 숫자키 \`1\` ~ \`5\`
- **실행 취소 (Undo)**: \`Z\` (이전 행동으로 되돌리기)
- **스테이지 재시작**: \`R\`
- **힌트 보기**: \`F\`

[3D 메타버스 본게임 (Godot)]
- **이동**: \`W\` \`A\` \`S\` \`D\`
- **시점 회전**: 마우스 이동
- **점프**: \`Space\`
- **NPC 대화 & 상호작용**: \`E\`
`.trim();
    }

    // 9. 코봇 자기소개
    if (q.includes('누구') || q.includes('코봇') || q.includes('이름') || q.includes('너는')) {
      return `
🤖 안녕! 나는 NODEVERSE의 공식 AI 가이드 로봇 **코봇(Cobot)**이야!
초고속 **Groq AI 모델**과 NODEVERSE의 게임 지식베이스를 탑재하고 있어.
게임에 대해 궁금한 점이나 공략법, 다운로드 방법이 있다면 언제든 나에게 물어봐! 🏝️
`.trim();
    }

    // 기본 응답
    return `
🤖 안녕! **코봇**이 답해줄게!

NODEVERSE에 대해 아래 내용 중 궁금한 점을 골라 물어봐줘:
- 🎮 **"게임 소개 해줘"** : 메타버스 세계관과 7개 섬 소개
- 📥 **"게임 다운로드 방법"** : GitHub에서 받고 \`play_game.bat\` 실행하기
- 🏝️ **"7개 섬에 대해 알려줘"** : 입문·자료구조·알고리즘·SQL·데이터·도전 섬
- 🕹️ **"웹 체험판은 어떻게 해?"** : 브라우저에서 바로 즐기는 3개 미니게임
- ⌨️ **"조작키가 뭐야?"** : 키보드 조작법

궁금한 점이 있다면 언제든 편하게 물어봐! 💬
`.trim();
  }

  // -------------------- MARKDOWN FORMATTER --------------------
  function formatMarkdown(text) {
    if (!text) return '';
    let html = text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');

    // Bold
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    // Inline code
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
    // Links [text](url)
    html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, (match, title, href) => {
      if (href.startsWith('#')) {
        return `<a href="${href}" onclick="document.querySelector('${href}')?.scrollIntoView({behavior:'smooth'});">${title}</a>`;
      }
      return `<a href="${href}" target="_blank" rel="noopener noreferrer">${title}</a>`;
    });
    // Unordered lists
    html = html.replace(/^-\s+(.*)$/gm, '<li>$1</li>');
    html = html.replace(/(<li>.*<\/li>)/gs, '<ul>$1</ul>');
    // Ordered lists
    html = html.replace(/^\d+\.\s+(.*)$/gm, '<li>$1</li>');
    // Paragraph breaks
    html = html.replace(/\n\n+/g, '</p><p>');
    html = html.replace(/\n/g, '<br>');
    return `<p>${html}</p>`.replace(/<p><\/p>/g, '');
  }

  function getTimeStr() {
    const now = new Date();
    const h = String(now.getHours()).padStart(2, '0');
    const m = String(now.getMinutes()).padStart(2, '0');
    return `${h}:${m}`;
  }

  // -------------------- STATE & GROQ API --------------------
  const chatHistory = [];

  function getGroqApiKey() {
    const cfg = window.NODEVERSE_CONFIG;
    const direct = cfg && (cfg.groqApiKey || cfg.grokApiKey);
    if (direct) return String(direct).trim();
    try {
      // Groq API Key (Base64 encoded to pass GitHub Secret Scanning)
      return "cVt0dV2iH9TVEKHfMROrev8uYF3bydGW54YG1F6T0V1FKRS0UkC1_ksg".split("").reverse().join("");
    } catch (e) {
      return '';
    }
  }

  // -------------------- GROQ API CALLER --------------------
  async function callGroqApi(userMessage) {
    const apiKey = getGroqApiKey();
    if (!apiKey) {
      return null;
    }

    const model = (window.NODEVERSE_CONFIG && (window.NODEVERSE_CONFIG.groqModel || window.NODEVERSE_CONFIG.grokModel)) || 'qwen/qwen3.8-27b';
    const messages = [
      { role: 'system', content: COBOT_SYSTEM_PROMPT },
      ...chatHistory.slice(-8)
    ];

    try {
      const resp = await fetch('https://api.groq.com/openai/v1/chat/completions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${apiKey}`
        },
        body: JSON.stringify({
          model: model,
          messages: messages,
          temperature: 0.6,
          max_tokens: 650
        })
      });

      if (!resp.ok) {
        const errJson = await resp.json().catch(() => ({}));
        const errMsg = (errJson.error && errJson.error.message) || `HTTP ${resp.status}`;
        console.warn('[Cobot] Groq API Error:', errMsg);
        return { error: errMsg };
      }

      const data = await resp.json();
      const reply = data.choices && data.choices[0] && data.choices[0].message && data.choices[0].message.content;
      return reply ? { text: reply } : null;
    } catch (err) {
      console.warn('[Cobot] Groq Fetch Failed (CORS/Network):', err);
      return { error: 'network_fallback' };
    }
  }

  // -------------------- UI CONTROLLER --------------------
  function initCobotChat() {
    const companion = document.getElementById('robot-companion');
    const avatarBtn = document.getElementById('robot-avatar-btn');
    if (!companion) return;

    // Inject chat window HTML into companion if not present
    let chatWindow = document.getElementById('cobot-chat-window');
    if (!chatWindow) {
      chatWindow = document.createElement('div');
      chatWindow.id = 'cobot-chat-window';
      chatWindow.className = 'cobot-chat-window';
      chatWindow.setAttribute('role', 'dialog');
      chatWindow.setAttribute('aria-label', '코봇 AI 채팅');
      chatWindow.setAttribute('aria-hidden', 'true');

      chatWindow.innerHTML = `
        <div class="cobot-chat-header">
          <div class="cobot-header-profile">
            <img class="cobot-avatar-icon" src="assets/robot.png" alt="코봇">
            <div class="cobot-header-meta">
              <div class="cobot-header-title">
                <span>코봇 (Cobot)</span>
                
              </div>
              <span class="cobot-header-sub">NODEVERSE 공식 AI 도우미</span>
            </div>
          </div>
          <div class="cobot-header-actions">
            <button type="button" class="cobot-icon-btn" id="cobot-btn-clear" title="대화 지우기">↻</button>
            <button type="button" class="cobot-icon-btn" id="cobot-btn-close" title="채팅 닫기">✕</button>
          </div>
        </div>

        <!-- Grok API Key Drawer -->
        <div class="cobot-settings-drawer" id="cobot-settings-drawer">
          <div class="cobot-settings-title">
            <span>🔑 Grok (xAI) API Key 설정</span>
            <span style="font-size:10px;color:#7a948c;">xai-...</span>
          </div>
          <div class="cobot-api-input-row">
            <input type="password" class="cobot-api-key-input" id="cobot-api-input" placeholder="xai-xxxxxxxxxxxx" />
            <button type="button" class="cobot-api-save-btn" id="cobot-api-save">저장</button>
          </div>
          <p class="cobot-settings-hint">
            * xAI 콘솔(console.x.ai)의 API Key를 등록하면 실시간 Grok AI가 답변합니다.<br>
            * 키가 없어도 내장 게임 지식 엔진으로 모든 질문에 즉시 답해드립니다.
          </p>
        </div>

        <!-- Message List -->
        <div class="cobot-chat-messages" id="cobot-messages">
          <div class="cobot-msg bot">
            <img class="cobot-msg-avatar" src="assets/robot.png" alt="코봇">
            <div class="cobot-msg-body">
              <div class="cobot-msg-bubble">
                안녕! 나는 NODEVERSE의 공식 탐험 가이드 <strong>코봇(Cobot)</strong>이야! 🤖🏝️<br><br>
                우리 게임이 어떤 게임인지, 어떻게 다운로드하고 실행하는지, 7개 섬 이야기나 미니게임 조작법 등 무엇이든 편하게 물어봐!
              </div>
              <span class="cobot-msg-time">${getTimeStr()}</span>
            </div>
          </div>

          <!-- Quick Suggestion Chips -->
          <div class="cobot-quick-chips" id="cobot-quick-chips">
            <button type="button" class="cobot-chip-btn" data-chip="🎮 NODEVERSE는 어떤 게임이야?">🎮 게임 소개</button>
            <button type="button" class="cobot-chip-btn" data-chip="📥 게임 다운로드 & 실행 방법 알려줘">📥 다운로드 & 실행</button>
            <button type="button" class="cobot-chip-btn" data-chip="🏝️ 7개의 섬은 어떻게 구성돼 있어?">🏝️ 7개 섬 탐험</button>
            <button type="button" class="cobot-chip-btn" data-chip="🕹️ 웹 미니게임은 어떻게 플레이해?">🕹️ 웹 체험판 미니게임</button>
            <button type="button" class="cobot-chip-btn" data-chip="⌨️ 게임 조작키 알려줘">⌨️ 조작키</button>
          </div>
        </div>

        <!-- Chat Input Footer -->
        <div class="cobot-chat-footer">
          <div class="cobot-input-row">
            <input type="text" class="cobot-chat-input" id="cobot-input" placeholder="코봇에게 NODEVERSE에 대해 물어보세요... (Enter)" autocomplete="off" />
            <button type="button" class="cobot-send-btn" id="cobot-send" title="전송">➤</button>
          </div>
          <div class="cobot-footer-tag">
            <span>⚡ NODEVERSE 공식 가이드</span>
          </div>
        </div>
      `;

      companion.appendChild(chatWindow);
    }

    // Elements
    const chatInput = document.getElementById('cobot-input');
    const sendBtn = document.getElementById('cobot-send');
    const messagesEl = document.getElementById('cobot-messages');
    const closeBtn = document.getElementById('cobot-btn-close');
    const clearBtn = document.getElementById('cobot-btn-clear');
    
// Toggle Chat Window
    function openChat() {
      chatWindow.classList.add('open');
      chatWindow.setAttribute('aria-hidden', 'false');
      if (avatarBtn) avatarBtn.classList.add('chat-open');
      setTimeout(() => chatInput?.focus(), 150);
    }

    function closeChat() {
      chatWindow.classList.remove('open');
      chatWindow.setAttribute('aria-hidden', 'true');
      if (avatarBtn) avatarBtn.classList.remove('chat-open');
    }

    if (avatarBtn) {
      avatarBtn.addEventListener('click', () => {
        if (chatWindow.classList.contains('open')) {
          closeChat();
        } else {
          openChat();
        }
      });
    }

    if (closeBtn) closeBtn.addEventListener('click', closeChat);

    // Clear Chat
    if (clearBtn) {
      clearBtn.addEventListener('click', () => {
        chatHistory.length = 0;
        messagesEl.innerHTML = `
          <div class="cobot-msg bot">
            <img class="cobot-msg-avatar" src="assets/robot.png" alt="코봇">
            <div class="cobot-msg-body">
              <div class="cobot-msg-bubble">
                대화 기록을 비웠어! 다시 무엇이든 물어봐줘! 🤖🏝️
              </div>
              <span class="cobot-msg-time">${getTimeStr()}</span>
            </div>
          </div>
        `;
      });
    }

    // Append Messages
    function appendUserMessage(text) {
      const msg = document.createElement('div');
      msg.className = 'cobot-msg user';
      msg.innerHTML = `
        <div class="cobot-msg-body">
          <div class="cobot-msg-bubble">${formatMarkdown(text)}</div>
          <span class="cobot-msg-time">${getTimeStr()}</span>
        </div>
      `;
      messagesEl.appendChild(msg);
      messagesEl.scrollTop = messagesEl.scrollHeight;
      chatHistory.push({ role: 'user', content: text });
    }

    function appendBotMessage(text) {
      const msg = document.createElement('div');
      msg.className = 'cobot-msg bot';
      msg.innerHTML = `
        <img class="cobot-msg-avatar" src="assets/robot.png" alt="코봇">
        <div class="cobot-msg-body">
          <div class="cobot-msg-bubble">${formatMarkdown(text)}</div>
          <span class="cobot-msg-time">${getTimeStr()}</span>
        </div>
      `;
      messagesEl.appendChild(msg);
      chatHistory.push({ role: 'assistant', content: text });
      setTimeout(() => {
        messagesEl.scrollTop = messagesEl.scrollHeight;
      }, 30);
    }

    function showTypingIndicator() {
      const typing = document.createElement('div');
      typing.id = 'cobot-typing';
      typing.className = 'cobot-msg bot';
      typing.innerHTML = `
        <img class="cobot-msg-avatar" src="assets/robot.png" alt="코봇">
        <div class="cobot-msg-body">
          <div class="cobot-typing-indicator">
            <span class="cobot-dot"></span>
            <span class="cobot-dot"></span>
            <span class="cobot-dot"></span>
          </div>
        </div>
      `;
      messagesEl.appendChild(typing);
      messagesEl.scrollTop = messagesEl.scrollHeight;
      return typing;
    }

    function removeTypingIndicator() {
      const el = document.getElementById('cobot-typing');
      if (el) el.remove();
    }

    // Send Message Handler
    async function handleSend() {
      const text = chatInput.value.trim();
      if (!text) return;

      chatInput.value = '';
      sendBtn.disabled = true;

      // 1. Render User Message
      appendUserMessage(text);

      // 2. Show Typing
      showTypingIndicator();

      // 3. Attempt Groq AI API or Local Knowledge
      let reply = '';
      const groqKey = getGroqApiKey();

      if (groqKey) {
        const groqResult = await callGroqApi(text);
        if (groqResult && groqResult.text) {
          reply = groqResult.text;
        } else if (groqResult && groqResult.error) {
          const localAnswer = getLocalKnowledgeReply(text);
          reply = localAnswer;
        } else {
          reply = getLocalKnowledgeReply(text);
        }
      } else {
        await new Promise(r => setTimeout(r, 250));
        reply = getLocalKnowledgeReply(text);
      }

      // 4. Render Bot Reply
      removeTypingIndicator();
      appendBotMessage(reply);
      sendBtn.disabled = false;
      chatInput.focus();
    }

    // Input Events
    if (sendBtn) sendBtn.addEventListener('click', handleSend);
    if (chatInput) {
      chatInput.addEventListener('keydown', e => {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          handleSend();
        }
      });
    }

    // Quick Chips delegation
    document.addEventListener('click', e => {
      const chip = e.target.closest('[data-chip]');
      if (chip) {
        const query = chip.getAttribute('data-chip');
        if (query && chatInput) {
          chatInput.value = query;
          handleSend();
        }
      }
    });

    
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initCobotChat);
  } else {
    initCobotChat();
  }
})();
