/* ==========================================================
   NODEVERSE — Authentic Godot 3-Island Mini-Game Web Trial
   1) 자료구조 섬: ST03 최근 작업 복구실 (스택 · LIFO)
   2) 알고리즘 섬: ALG01 순서 맞춤 작업대 (버블 · 선택 · 삽입 정렬)
   3) SQL 섬: SQL01 필요한 칸만 꺼내기 (5×5 서랍 색칠)
   ========================================================== */

(function () {
  'use strict';

  /* -------------------- SHARED CONSTANTS -------------------- */
  const SQL_COLUMNS = ['id', 'name', 'score', 'dept', 'city'];
  const SQL_ROWS = [
    { id: 1, name: '민지', score: 90, dept: '개발', city: '서울' },
    { id: 2, name: '준호', score: 55, dept: '디자인', city: '부산' },
    { id: 3, name: '서연', score: 80, dept: '개발', city: '서울' },
    { id: 4, name: '도윤', score: null, dept: '디자인', city: '서울' },
    { id: 5, name: '하늘', score: 70, dept: '기획', city: '대전' }
  ];

  const ISLAND_META = {
    ds: {
      stageId: 'ST03',
      stageName: '최근 작업 복구실 (스택 · LIFO)',
      bg: 'assets/stages/st03.png',
      npcName: '복구실 장인',
      npcAvatar: 'assets/npcs/npc03.png',
      controlsHtml:
        '마우스 클릭 또는 <kbd>W</kbd><kbd>A</kbd><kbd>S</kbd><kbd>D</kbd> / 방향키 이동 · <kbd>E</kbd> 상호작용 · <kbd>Z</kbd> 되돌리기 · <kbd>R</kbd> 다시 시작',
      levels: [
        {
          label: '1단계 · Top 확인과 역순',
          mission: 'A → B를 타워에 쌓고, 확인대(Peek)에서 Top을 확인한 뒤 B → A 순서로 작업대에 올리세요.',
          npcIntro:
            '입고 레일에서 A, B를 차례로 가져와 스택 타워에 쌓아 봐! 그다음 가운데 확인대(Peek)에서 맨 위(Top)가 B인지 확인하고 B → A 순서로 꺼내면 돼.',
          hint: '힌트: 1) 입고 레일(A) → 스택 타워  2) 입고 레일(B) → 스택 타워  3) Top 확인대 클릭(Peek)  4) 스택 타워(B) → 결과 작업대  5) 스택 타워(A) → 결과 작업대!',
          incoming: ['A', 'B'],
          target: ['B', 'A'],
          cap: 3,
          requirePeek: true
        },
        {
          label: '2단계 · 3개 완전 역순',
          mission: 'A → B → C를 모두 스택에 쌓았다가 C → B → A 순서로 결과 작업대에 복구하세요.',
          npcIntro:
            '가장 마지막에 들어간 상자가 가장 먼저 나오는 후입선출(LIFO)! A, B, C를 끝까지 쌓은 뒤 위에서부터 하나씩 꺼내 C → B → A를 완성해 봐.',
          hint: '힌트: A, B, C 세 상자를 모두 스택 타워에 넣은(push) 다음, 타워에서 C → B → A 순서대로 꺼내(pop) 아래쪽 결과 작업대에 놓으세요.',
          incoming: ['A', 'B', 'C'],
          target: ['C', 'B', 'A'],
          cap: 3,
          requirePeek: false
        },
        {
          label: '3단계 · 중간에 먼저 꺼내기',
          mission: '넣는 타이밍과 꺼내는 타이밍을 조절해 B → C → A 순서를 만드세요.',
          npcIntro:
            '무조건 끝까지 다 쌓을 필요는 없어! A, B를 쌓은 뒤 B를 먼저 꺼내 작업대에 두고, 그다음 C를 쌓았다가 꺼내면 B → C → A가 만들어지지!',
          hint: '힌트: 1) A push → 2) B push → 3) B pop & 결과 작업대 등록 → 4) C push → 5) C pop & 결과 등록 → 6) A pop & 결과 등록!',
          incoming: ['A', 'B', 'C'],
          target: ['B', 'C', 'A'],
          cap: 3,
          requirePeek: false
        }
      ]
    },
    algo: {
      stageId: 'ALG01',
      stageName: '순서 맞춤 작업대 (정렬 3종)',
      bg: 'assets/stages/alg01.png',
      npcName: '작업대 관리인',
      npcAvatar: 'assets/npcs/npc01.png',
      controlsHtml:
        '상자/버튼 클릭 또는 <kbd>←</kbd><kbd>→</kbd> 이동 · <kbd>1</kbd><kbd>2</kbd><kbd>3</kbd> / <kbd>E</kbd> 단계 실행 · <kbd>Z</kbd> 되돌리기 · <kbd>R</kbd> 초기화',
      levels: [
        {
          label: '1단계 · 버블 정렬',
          mode: 'bubble',
          banner: '버블 정렬 (Bubble Sort) — 인접한 두 상자를 비교해 왼쪽이 더 크면 교환!',
          mission: '이웃한 두 상자를 앞에서부터 차례로 비교하며 [5, 2, 4, 1]을 [1, 2, 4, 5]로 정렬하세요.',
          npcIntro:
            '버블 정렬은 바로 옆 상자끼리만 비교해! 왼쪽 값이 오른쪽 값보다 크면 [두 값 교환(Swap)], 아니면 [그대로 통과(Keep)] 버튼을 눌러 큰 값을 오른쪽 끝으로 보내자.',
          hint: '힌트: 노란 테두리로 강조된 두 상자 중 왼쪽 숫자가 오른쪽 숫자보다 크면 [⇄ 두 값 교환], 작거나 같으면 [→ 그대로 통과]를 누르세요.',
          initial: [5, 2, 4, 1]
        },
        {
          label: '2단계 · 선택 정렬',
          mode: 'selection',
          banner: '선택 정렬 (Selection Sort) — 남은 구간에서 가장 작은 상자를 골라 앞자리와 교환!',
          mission: '미정렬 구간에서 최솟값 상자를 직접 클릭해 앞에서부터 차례대로 [1, 3, 3, 6, 7]을 완성하세요.',
          npcIntro:
            '선택 정렬은 아직 정리되지 않은 구간에서 가장 작은 값을 한 번에 찾아 맨 앞자리와 맞바꾸는 방식이야. 남은 상자들 중 최솟값 상자를 클릭해 봐!',
          hint: '힌트: 초록색(확정) 상자 오른쪽에 있는 미정렬 상자들 가운데 숫자가 가장 작은 상자를 클릭하세요! (동일한 최솟값 3은 어느 쪽을 골라도 됩니다)',
          initial: [7, 3, 3, 6, 1]
        },
        {
          label: '3단계 · 삽입 정렬',
          mode: 'insertion',
          banner: '삽입 정렬 (Insertion Sort) — 새 카드를 들어 올린 뒤 큰 값들을 오른쪽으로 밀어 빈칸에 삽입!',
          mission: '현재 상자를 들어 올리고(Lift), 앞쪽의 더 큰 값들을 오른쪽으로 민 뒤(Shift) 알맞은 빈칸에 꽂으세요(Insert).',
          npcIntro:
            '손안의 카드를 정렬하듯! 1) 새 상자를 들고, 2) 빈칸 왼쪽 값이 들고 있는 값보다 크면 오른쪽으로 밀고, 3) 작거나 같으면 그 자리에 꽂으면 돼!',
          hint: '힌트: 먼저 [1. 새 카드 들기]를 누른 뒤, 빈칸 왼쪽 숫자가 손에 든 숫자보다 크면 [2. 큰 값 오른쪽 밀기], 아니면 [3. 빈칸에 카드 꽂기]를 누르세요.',
          initial: [9, -2, 5, 0, 3, 1]
        }
      ]
    },
    sql: {
      stageId: 'SQL01',
      stageName: '필요한 칸만 꺼내기 (5×5 서랍 색칠)',
      bg: 'assets/stages/sql01.png',
      npcName: '서랍 기록관',
      npcAvatar: 'assets/npcs/npc05.png',
      controlsHtml:
        '셀/헤더 클릭 또는 <kbd>WASD</kbd> 이동 + <kbd>E</kbd> 칠하기 · 도구 <kbd>1</kbd>~<kbd>5</kbd> 전환 · <kbd>Enter</kbd> 쿼리 제출',
      levels: [
        {
          label: '1단계 · SELECT 열 고르기',
          mission: 'students 테이블에서 학생들의 이름(name)과 점수(score) 열만 파란 붓으로 칠해 제출하세요.',
          npcIntro:
            '1번 파란 붓(SELECT)은 가져올 열(Column)을 고르는 도구야! 상단 헤더나 칸에서 name 열과 score 열을 클릭해 파랗게 칠하고 [제출]을 눌러 봐.',
          hint: '힌트: [1. 열 붓(SELECT)] 상태에서 name 열과 score 열을 클릭하세요. 모든 행(1~5행)이 기본 포함되어 교차 칸이 초록색으로 빛납니다. 그 후 [제출] 클릭!',
          targetCols: ['name', 'score'],
          targetRows: [0, 1, 2, 3, 4],
          requireWhere: false,
          targetOrderDesc: false,
          targetLimitOne: false
        },
        {
          label: '2단계 · WHERE 조건과 NULL 주의',
          mission: '점수(score)가 80점 이상인 학생의 이름(name)과 점수(score)만 초록색 교차 칸으로 남기세요. (4행 도윤의 NULL 주의!)',
          npcIntro:
            '이번엔 1번 파란 붓으로 name, score 열을 고르고, 2번 금색 붓(WHERE)으로 score >= 80인 행(1행 민지 90점, 3행 서연 80점)만 칠해 봐! NULL은 숫자가 아니라 조건에서 제외돼.',
          hint: '힌트: 1번 파란 붓으로 name, score 열 선택 → 2번 금색 붓으로 1행(민지 90)과 3행(서연 80) 클릭 → 초록색 교차 칸 4개가 만들어지면 [제출] 클릭!',
          targetCols: ['name', 'score'],
          targetRows: [0, 2],
          requireWhere: true,
          targetOrderDesc: false,
          targetLimitOne: false
        },
        {
          label: '3단계 · ORDER BY + LIMIT 1',
          mission: '점수 60점 이상(민지·서연·하늘) 중 점수 내림차순(ORDER BY) 1등 1명(LIMIT 1)의 name, score를 추출하세요!',
          npcIntro:
            '실전 쿼리 완성! name, score 열(파랑) + 60점 이상인 1·3·5행(금색)을 칠한 뒤, 4번 [ORDER BY score DESC]와 5번 [LIMIT 1] 스위치를 켜고 제출해 봐!',
          hint: '힌트: 파란 붓(name, score) + 금색 붓(1행 민지, 3행 서연, 5행 하늘) + [4. ORDER BY DESC] 켜기 + [5. LIMIT 1] 켜기 → [제출]!',
          targetCols: ['name', 'score'],
          targetRows: [0, 2, 4],
          requireWhere: true,
          targetOrderDesc: true,
          targetLimitOne: true
        }
      ]
    }
  };

  /* -------------------- GLOBAL STATE -------------------- */
  const state = {
    island: 'ds',
    levelIndex: { ds: 0, algo: 0, sql: 0 },
    cleared: {
      ds: [false, false, false],
      algo: [false, false, false],
      sql: [false, false, false]
    },
    ds: null,
    algo: null,
    sql: null
  };

  /* -------------------- INITIALIZERS -------------------- */
  function initDsLevel(lvlIdx) {
    const lvl = ISLAND_META.ds.levels[lvlIdx];
    state.ds = {
      incoming: lvl.incoming.slice(),
      stack: [],
      output: [],
      held: '',
      heldSource: '', // 'intake' | 'tower'
      peeked: false,
      lastPeekVal: null,
      focusStation: 'intake', // 'intake' | 'tower' | 'desk' | 'output'
      robotPos: { left: '78%', top: '148px' },
      codeLogs: ['# ST03 스택 복구실 준비 완료', 'stack = Stack(capacity=3)', 'result = []'],
      history: [],
      speech: lvl.npcIntro,
      speechTone: ''
    };
  }

  function initAlgoLevel(lvlIdx) {
    const lvl = ISLAND_META.algo.levels[lvlIdx];
    const arr = lvl.initial.slice();
    state.algo = {
      mode: lvl.mode,
      arr: arr,
      comparisons: 0,
      writes: 0,
      // bubble state
      passIdx: 0,
      cursor: 0,
      // selection state
      sortedCount: 0,
      selectedCrate: 0,
      // insertion state
      insIndex: 1,
      liftedKey: null,
      holeIndex: -1,
      codeLines: [
        `# ${lvl.label}`,
        `arr = [${arr.join(', ')}]`
      ],
      history: [],
      speech: lvl.npcIntro,
      speechTone: ''
    };
  }

  function initSqlLevel(lvlIdx) {
    const lvl = ISLAND_META.sql.levels[lvlIdx];
    state.sql = {
      tool: 'select', // 'select' | 'where' | 'eraser'
      selectedCols: [],
      selectedRows: [],
      orderDesc: false,
      limitOne: false,
      cursorRow: 0,
      cursorCol: 1,
      history: [],
      speech: lvl.npcIntro,
      speechTone: ''
    };
  }

  /* -------------------- SNAPSHOT / UNDO -------------------- */
  function pushHistory(islandKey) {
    const cur = state[islandKey];
    if (!cur) return;
    const clone = JSON.parse(JSON.stringify(cur));
    delete clone.history;
    cur.history.push(clone);
    if (cur.history.length > 30) cur.history.shift();
  }

  function undoCurrent() {
    const cur = state[state.island];
    if (!cur || !cur.history || cur.history.length === 0) {
      setSpeech(state.island, '되돌릴 이전 작업이 없어!', '');
      renderAll();
      return;
    }
    const prev = cur.history.pop();
    prev.history = cur.history;
    state[state.island] = prev;
    setSpeech(state.island, '직전 행동을 한 단계 되돌렸어 (Undo).', '');
    renderAll();
  }

  function setSpeech(islandKey, text, tone) {
    if (state[islandKey]) {
      state[islandKey].speech = text;
      state[islandKey].speechTone = tone || '';
    }
  }

  /* ==========================================================
     1. DS ISLAND: ST03 STACK LOGIC
     ========================================================== */
  const DS_STATION_POS = {
    intake: { left: '72%', top: '215px' },
    tower: { left: '31%', top: '235px' },
    desk: { left: '47%', top: '268px' },
    output: { left: '54%', top: '375px' }
  };

  function interactDsStation(station) {
    const ds = state.ds;
    const lvlIdx = state.levelIndex.ds;
    const lvl = ISLAND_META.ds.levels[lvlIdx];
    ds.focusStation = station;
    ds.robotPos = DS_STATION_POS[station] || DS_STATION_POS.intake;

    if (station === 'intake') {
      if (ds.held) {
        if (ds.heldSource === 'intake') {
          pushHistory('ds');
          ds.incoming.unshift(ds.held);
          ds.codeLogs.push(`# '${ds.held}' 상자를 입고 레일에 다시 내려놓음`);
          ds.held = '';
          ds.heldSource = '';
          setSpeech('ds', '들고 있던 상자를 입고 레일에 다시 내려놓았어.', '');
        } else {
          setSpeech('ds', '스택 타워에서 꺼낸 상자는 아래쪽 [복구 결과 작업대]나 [스택 타워]에 놓아야 해!', 'wrong');
        }
      } else {
        if (ds.incoming.length === 0) {
          setSpeech('ds', '입고 레일에 남은 상자가 없어! 이제 스택 타워에서 상자를 꺼내자.', '');
        } else {
          pushHistory('ds');
          const item = ds.incoming.shift();
          ds.held = item;
          ds.heldSource = 'intake';
          ds.codeLogs.push(`hand = intake.take()  # '${item}' 집기`);
          setSpeech('ds', `'${item}' 상자를 집었어! 이제 왼쪽 [스택 타워]를 클릭해 위로 쌓아 올려 봐 (push).`, '');
        }
      }
    } else if (station === 'tower') {
      if (ds.held) {
        if (ds.stack.length >= lvl.cap) {
          setSpeech('ds', '스택 타워가 가득 찼어 (Stack Overflow)! 먼저 맨 위 상자를 꺼내야 해.', 'wrong');
        } else {
          pushHistory('ds');
          const item = ds.held;
          ds.stack.push(item);
          ds.held = '';
          ds.heldSource = '';
          ds.codeLogs.push(`stack.push("${item}")   # top -> '${item}' (size=${ds.stack.length})`);
          setSpeech('ds', `stack.push("${item}") 성공! 현재 맨 위(Top) 상자는 '${item}'이야.`, '');
        }
      } else {
        if (ds.stack.length === 0) {
          setSpeech('ds', '스택 타워가 비어 있어 (Stack Underflow)! 입고 레일에서 상자를 먼저 가져오자.', 'wrong');
        } else {
          pushHistory('ds');
          const topItem = ds.stack.pop();
          ds.held = topItem;
          ds.heldSource = 'tower';
          ds.codeLogs.push(`hand = stack.pop()    # '${topItem}' 꺼내기`);
          setSpeech('ds', `맨 위 상자 '${topItem}'을 꺼냈어(pop)! 아래쪽 [복구 결과 작업대]를 클릭해 등록해 봐.`, '');
        }
      }
    } else if (station === 'desk') {
      if (ds.stack.length === 0) {
        setSpeech('ds', '스택이 비어 있어서 확인할 Top이 없어! 먼저 상자를 타워에 쌓아 봐.', 'wrong');
      } else {
        pushHistory('ds');
        const topVal = ds.stack[ds.stack.length - 1];
        ds.peeked = true;
        ds.lastPeekVal = topVal;
        ds.codeLogs.push(`top = stack.peek()    # '${topVal}' 확인 (꺼내지 않음)`);
        setSpeech('ds', `stack.peek() 확인 완료! 꺼내지 않고 살펴본 현재 Top은 '${topVal}'이야.`, 'good');
      }
    } else if (station === 'output') {
      if (!ds.held) {
        setSpeech('ds', '결과 작업대에 올릴 상자를 들고 있지 않아! 스택 타워에서 맨 위 상자를 먼저 꺼내 와.', 'wrong');
      } else if (ds.heldSource !== 'tower') {
        setSpeech(
          'ds',
          '입고 레일에서 바로 작업대로 가져올 순 없어! 반드시 [스택 타워]에 push했다가 pop해서 옮겨야 해.',
          'wrong'
        );
      } else {
        const expected = lvl.target[ds.output.length];
        if (ds.held !== expected) {
          setSpeech(
            'ds',
            `지금 작업대 ${ds.output.length + 1}번째 자리에 필요한 상자는 '${expected}'인데 들고 있는 건 '${ds.held}'이야! 타워에 다시 넣거나 Z로 되돌려 봐.`,
            'wrong'
          );
        } else {
          pushHistory('ds');
          const item = ds.held;
          ds.output.push(item);
          ds.held = '';
          ds.heldSource = '';
          ds.codeLogs.push(`result.append("${item}")  # [${ds.output.map(x => '"' + x + '"').join(', ')}]`);

          if (ds.output.length === lvl.target.length) {
            if (lvl.requirePeek && !ds.peeked) {
              setSpeech(
                'ds',
                '순서는 맞았지만 1단계 미션 조건인 [Top 확인대(Peek)]를 한 번도 안 눌렀어! Z로 되돌려 Peek을 먼저 해 봐.',
                'wrong'
              );
            } else {
              state.cleared.ds[lvlIdx] = true;
              ds.codeLogs.push(`# ★ STAGE CLEAR! 목표 순서 [${lvl.target.join(' → ')}] 완성!`);
              setSpeech(
                'ds',
                `🎉 완벽해! 후입선출(LIFO) 원리로 [${lvl.target.join(' → ')}] 복구에 성공했어! (다음 단계 버튼 클릭)`,
                'good'
              );
            }
          } else {
            setSpeech('ds', `좋아! '${item}' 등록 완료! 다음 목표 상자는 '${lvl.target[ds.output.length]}'이야.`, 'good');
          }
        }
      }
    }

    renderAll();
  }

  /* ==========================================================
     2. ALGO ISLAND: ALG01 SORTING LOGIC
     ========================================================== */
  function isSortedAsc(arr) {
    for (let i = 1; i < arr.length; i++) {
      if (arr[i - 1] > arr[i]) return false;
    }
    return true;
  }

  function algoBubbleStep(doSwap) {
    const al = state.algo;
    const lvlIdx = state.levelIndex.algo;
    const n = al.arr.length;
    if (al.passIdx >= n - 1 || isSortedAsc(al.arr)) {
      state.cleared.algo[lvlIdx] = true;
      setSpeech('algo', '🎉 이미 오름차순 정렬이 모두 끝났어! 다음 정렬 단계로 넘어가 보자.', 'good');
      renderAll();
      return;
    }

    const j = al.cursor;
    const leftVal = al.arr[j];
    const rightVal = al.arr[j + 1];
    const needSwap = leftVal > rightVal;

    if (doSwap !== needSwap) {
      if (needSwap) {
        setSpeech(
          'algo',
          `비교 중인 [${leftVal}, ${rightVal}]에서 왼쪽(${leftVal})이 오른쪽(${rightVal})보다 크니까 [⇄ 두 값 교환(Swap)]을 눌러야 해!`,
          'wrong'
        );
      } else {
        setSpeech(
          'algo',
          `비교 중인 [${leftVal}, ${rightVal}]은 이미 ${leftVal} ≤ ${rightVal} 순서가 맞으니까 교환하지 말고 [→ 그대로 통과(Keep)]를 눌러야 해!`,
          'wrong'
        );
      }
      renderAll();
      return;
    }

    pushHistory('algo');
    al.comparisons += 1;
    if (doSwap) {
      al.arr[j] = rightVal;
      al.arr[j + 1] = leftVal;
      al.writes += 2;
      al.codeLines.push(`# cmp(${leftVal}, ${rightVal}) -> Swap!`);
      al.codeLines.push(`arr[${j}], arr[${j + 1}] = ${rightVal}, ${leftVal}`);
    } else {
      al.codeLines.push(`# cmp(${leftVal}, ${rightVal}) -> Keep`);
    }

    al.cursor += 1;
    const limit = n - 1 - al.passIdx;
    if (al.cursor >= limit) {
      al.passIdx += 1;
      al.cursor = 0;
    }

    if (isSortedAsc(al.arr) || al.passIdx >= n - 1) {
      al.passIdx = n - 1;
      state.cleared.algo[lvlIdx] = true;
      al.codeLines.push(`# ★ 버블 정렬 완료: [${al.arr.join(', ')}]`);
      setSpeech(
        'algo',
        `🎉 버블 정렬 성공! 총 비교 ${al.comparisons}회, 기록 ${al.writes}회로 [${al.arr.join(', ')}] 정렬을 마쳤어!`,
        'good'
      );
    } else {
      const nextA = al.arr[al.cursor];
      const nextB = al.arr[al.cursor + 1];
      setSpeech(
        'algo',
        `좋아! 다음 인접 쌍은 index ${al.cursor}(${nextA})와 index ${al.cursor + 1}(${nextB})이야. 교환할지 통과할지 선택해 봐!`,
        'good'
      );
    }
    renderAll();
  }

  function algoSelectionPick(idx) {
    const al = state.algo;
    const lvlIdx = state.levelIndex.algo;
    const n = al.arr.length;
    al.selectedCrate = idx;

    if (al.sortedCount >= n - 1) {
      state.cleared.algo[lvlIdx] = true;
      renderAll();
      return;
    }

    if (idx < al.sortedCount) {
      setSpeech('algo', `index ${idx}번 상자는 이미 앞쪽에 확정된 구간이야! index ${al.sortedCount}~${n - 1} 중에서 골라 봐.`, 'wrong');
      renderAll();
      return;
    }

    let minVal = Infinity;
    for (let k = al.sortedCount; k < n; k++) {
      if (al.arr[k] < minVal) minVal = al.arr[k];
    }

    if (al.arr[idx] !== minVal) {
      setSpeech(
        'algo',
        `남은 미정렬 구간 [${al.sortedCount}..${n - 1}]에서 가장 작은 값은 ${minVal}이야! ${al.arr[idx]} 대신 최솟값(${minVal}) 상자를 골라 봐.`,
        'wrong'
      );
      renderAll();
      return;
    }

    pushHistory('algo');
    const targetPos = al.sortedCount;
    al.comparisons += n - al.sortedCount - 1;
    if (idx !== targetPos) {
      const tmp = al.arr[targetPos];
      al.arr[targetPos] = al.arr[idx];
      al.arr[idx] = tmp;
      al.writes += 2;
      al.codeLines.push(`min_idx = ${idx}  # 최솟값 ${minVal}`);
      al.codeLines.push(`arr[${targetPos}], arr[${idx}] = ${al.arr[targetPos]}, ${al.arr[idx]}`);
    } else {
      al.codeLines.push(`min_idx = ${idx}  # 제자리 유지 (${minVal})`);
    }

    al.sortedCount += 1;
    al.selectedCrate = al.sortedCount;

    if (al.sortedCount >= n - 1 || isSortedAsc(al.arr)) {
      al.sortedCount = n;
      state.cleared.algo[lvlIdx] = true;
      al.codeLines.push(`# ★ 선택 정렬 완료: [${al.arr.join(', ')}]`);
      setSpeech(
        'algo',
        `🎉 선택 정렬 완성! 매 단계 최솟값을 정확히 골라 [${al.arr.join(', ')}]을 완성했어!`,
        'good'
      );
    } else {
      setSpeech(
        'algo',
        `정확해! index ${targetPos} 자리에 최솟값 ${minVal} 확정! 이제 남은 구간 [${al.sortedCount}..${n - 1}]에서 다음 최솟값을 클릭해 봐.`,
        'good'
      );
    }
    renderAll();
  }

  function algoInsertionAction(action) {
    const al = state.algo;
    const lvlIdx = state.levelIndex.algo;
    const n = al.arr.length;

    if (al.insIndex >= n && al.liftedKey === null) {
      state.cleared.algo[lvlIdx] = true;
      renderAll();
      return;
    }

    if (action === 'lift') {
      if (al.liftedKey !== null) {
        setSpeech('algo', `이미 손에 카드(${al.liftedKey})를 들고 있어! 왼쪽 값을 밀거나(Shift) 빈칸에 꽂아(Insert) 봐.`, 'wrong');
        renderAll();
        return;
      }
      pushHistory('algo');
      al.liftedKey = al.arr[al.insIndex];
      al.holeIndex = al.insIndex;
      al.writes += 1;
      al.codeLines.push(`key = arr[${al.insIndex}]  # ${al.liftedKey} 들기`);
      setSpeech(
        'algo',
        `카드 ${al.liftedKey}을 손에 들었어! 빈칸 왼쪽 값(${al.arr[al.holeIndex - 1]})과 비교해서 더 크면 [오른쪽으로 밀기], 아니면 [빈칸에 꽂기]를 눌러 봐.`,
        ''
      );
    } else if (action === 'shift') {
      if (al.liftedKey === null) {
        setSpeech('algo', '먼저 [1. 새 카드 들기] 버튼을 눌러 이번 차례 상자를 손에 들어야 해!', 'wrong');
        renderAll();
        return;
      }
      if (al.holeIndex <= 0) {
        setSpeech('algo', '더 이상 왼쪽에 비교할 상자가 없어(index 0)! [3. 빈칸에 카드 꽂기]를 눌러 카드를 내려놓자.', 'wrong');
        renderAll();
        return;
      }
      const leftVal = al.arr[al.holeIndex - 1];
      if (leftVal <= al.liftedKey) {
        setSpeech(
          'algo',
          `왼쪽 값(${leftVal})이 손에 든 카드(${al.liftedKey})보다 크지 않아(${leftVal} ≤ ${al.liftedKey})! 더 밀지 말고 [3. 빈칸에 카드 꽂기]를 눌러야 해.`,
          'wrong'
        );
        renderAll();
        return;
      }
      pushHistory('algo');
      al.comparisons += 1;
      al.arr[al.holeIndex] = leftVal;
      al.holeIndex -= 1;
      al.writes += 1;
      al.codeLines.push(`arr[${al.holeIndex + 1}] = arr[${al.holeIndex}]  # ${leftVal} 오른쪽 밀기`);
      if (al.holeIndex > 0 && al.arr[al.holeIndex - 1] > al.liftedKey) {
        setSpeech('algo', `${leftVal}을 오른쪽으로 밀었어! 그 왼쪽 값(${al.arr[al.holeIndex - 1]})도 ${al.liftedKey}보다 크니 한 번 더 밀어 볼까?`, 'good');
      } else {
        setSpeech('algo', `${leftVal}을 오른쪽으로 밀었어! 이제 알맞은 자리를 찾았으니 [3. 빈칸에 카드 꽂기]를 눌러 봐!`, 'good');
      }
    } else if (action === 'insert') {
      if (al.liftedKey === null) {
        setSpeech('algo', '손에 든 카드가 없어! 먼저 [1. 새 카드 들기]를 눌러 카드를 들어 올려 봐.', 'wrong');
        renderAll();
        return;
      }
      if (al.holeIndex > 0 && al.arr[al.holeIndex - 1] > al.liftedKey) {
        setSpeech(
          'algo',
          `아직 빈칸 왼쪽 값(${al.arr[al.holeIndex - 1]})이 손에 든 카드(${al.liftedKey})보다 커! 먼저 [2. 큰 값 오른쪽 밀기]로 자리를 비워야 해.`,
          'wrong'
        );
        renderAll();
        return;
      }
      pushHistory('algo');
      if (al.holeIndex > 0) al.comparisons += 1;
      al.arr[al.holeIndex] = al.liftedKey;
      al.writes += 1;
      al.codeLines.push(`arr[${al.holeIndex}] = ${al.liftedKey}       # 빈칸에 삽입 완료`);
      const placedVal = al.liftedKey;
      al.liftedKey = null;
      al.holeIndex = -1;
      al.insIndex += 1;

      if (al.insIndex >= n) {
        state.cleared.algo[lvlIdx] = true;
        al.codeLines.push(`# ★ 삽입 정렬 완료: [${al.arr.join(', ')}]`);
        setSpeech('algo', `🎉 삽입 정렬 마스터! 모든 카드를 제자리에 꽂아 [${al.arr.join(', ')}]을 완성했어!`, 'good');
      } else {
        setSpeech('algo', `좋아! 카드 ${placedVal} 삽입 완료! 이제 다음 카드(index ${al.insIndex}, 값 ${al.arr[al.insIndex]})를 들어 올려 보자.`, 'good');
      }
    }

    renderAll();
  }

  /* ==========================================================
     3. SQL ISLAND: SQL01 5x5 DRAWER LOGIC
     ========================================================== */
  function toggleSqlColumn(colName) {
    const sq = state.sql;
    pushHistory('sql');
    const idx = sq.selectedCols.indexOf(colName);
    if (idx >= 0) {
      sq.selectedCols.splice(idx, 1);
      setSpeech('sql', `SELECT 절에서 '${colName}' 열을 제외했어.`, '');
    } else {
      sq.selectedCols.push(colName);
      setSpeech('sql', `SELECT 절에 '${colName}' 열을 추가했어! (선택 순서: ${sq.selectedCols.join(', ')})`, '');
    }
    renderAll();
  }

  function toggleSqlRow(rowIdx) {
    const sq = state.sql;
    pushHistory('sql');
    const idx = sq.selectedRows.indexOf(rowIdx);
    const rowData = SQL_ROWS[rowIdx];
    if (idx >= 0) {
      sq.selectedRows.splice(idx, 1);
      setSpeech('sql', `${rowIdx + 1}행(${rowData.name})의 WHERE 조건 선택을 해제했어.`, '');
    } else {
      sq.selectedRows.push(rowIdx);
      sq.selectedRows.sort((a, b) => a - b);
      if (rowData.score === null) {
        setSpeech(
          'sql',
          `⚠️ 주의: ${rowIdx + 1}행(${rowData.name})의 score는 NULL(비어 있음)이야! 숫자 비교(score >= 80 등)에서는 NULL이 통과하지 못해.`,
          'wrong'
        );
      } else {
        setSpeech('sql', `${rowIdx + 1}행(${rowData.name}, score=${rowData.score})을 WHERE 조건 통과 행(금색)으로 칠했어!`, '');
      }
    }
    renderAll();
  }

  function paintSqlCell(rIdx, cIdx) {
    const sq = state.sql;
    sq.cursorRow = rIdx;
    sq.cursorCol = cIdx;
    const colName = SQL_COLUMNS[cIdx];

    if (sq.tool === 'select') {
      toggleSqlColumn(colName);
    } else if (sq.tool === 'where') {
      toggleSqlRow(rIdx);
    } else if (sq.tool === 'eraser') {
      pushHistory('sql');
      const ci = sq.selectedCols.indexOf(colName);
      if (ci >= 0) sq.selectedCols.splice(ci, 1);
      const ri = sq.selectedRows.indexOf(rIdx);
      if (ri >= 0) sq.selectedRows.splice(ri, 1);
      setSpeech('sql', `지우개로 ${rIdx + 1}행 / '${colName}' 열의 색칠을 지웠어.`, '');
      renderAll();
    }
  }

  function getEffectiveSqlRows() {
    const sq = state.sql;
    const lvl = ISLAND_META.sql.levels[state.levelIndex.sql];
    if (!lvl.requireWhere && sq.selectedRows.length === 0) {
      return [0, 1, 2, 3, 4];
    }
    return sq.selectedRows.slice();
  }

  function buildLiveSqlText() {
    const sq = state.sql;
    const lvlIdx = state.levelIndex.sql;
    const lvl = ISLAND_META.sql.levels[lvlIdx];
    const colsPart = sq.selectedCols.length > 0 ? sq.selectedCols.join(', ') : '/* 열을 칠하세요 */';
    let lines = [`SELECT ${colsPart}`, `FROM students`];

    if (lvl.requireWhere || sq.selectedRows.length > 0) {
      if (sq.selectedRows.length === 0) {
        lines.push(`WHERE /* 금색 붓으로 조건에 맞는 행을 칠하세요 */`);
      } else if (
        lvlIdx === 1 &&
        sq.selectedRows.length === 2 &&
        sq.selectedRows[0] === 0 &&
        sq.selectedRows[1] === 2
      ) {
        lines.push(`WHERE score >= 80`);
      } else if (
        lvlIdx === 2 &&
        sq.selectedRows.length === 3 &&
        sq.selectedRows[0] === 0 &&
        sq.selectedRows[1] === 2 &&
        sq.selectedRows[2] === 4
      ) {
        lines.push(`WHERE score >= 60`);
      } else {
        const names = sq.selectedRows.map(r => `'${SQL_ROWS[r].name}'`).join(', ');
        lines.push(`WHERE name IN (${names})`);
      }
    }

    if (sq.orderDesc) {
      lines.push(`ORDER BY score DESC`);
    }
    if (sq.limitOne) {
      lines.push(`LIMIT 1`);
    }
    return lines.join('\n') + ';';
  }

  function submitSqlQuery() {
    const sq = state.sql;
    const lvlIdx = state.levelIndex.sql;
    const lvl = ISLAND_META.sql.levels[lvlIdx];

    // Check columns
    if (sq.selectedCols.length === 0) {
      setSpeech('sql', '아직 파란 붓(SELECT)으로 선택한 열이 없어! name과 score 열을 먼저 칠해 봐.', 'wrong');
      renderAll();
      return;
    }

    const sameCols =
      sq.selectedCols.length === lvl.targetCols.length &&
      sq.selectedCols.every((c, i) => c === lvl.targetCols[i]);

    if (!sameCols) {
      const hasSameSet =
        sq.selectedCols.length === lvl.targetCols.length &&
        lvl.targetCols.every(c => sq.selectedCols.includes(c));
      if (hasSameSet) {
        setSpeech(
          'sql',
          `열 종류는 맞았지만 선택 순서가 [${sq.selectedCols.join(', ')}]로 반대야! [${lvl.targetCols.join(', ')}] 순서로 다시 칠해 봐.`,
          'wrong'
        );
      } else {
        setSpeech(
          'sql',
          `선택된 열([${sq.selectedCols.join(', ')}])이 미션 목표([${lvl.targetCols.join(', ')}])와 달라! 파란 붓으로 필요한 열만 칠해 봐.`,
          'wrong'
        );
      }
      renderAll();
      return;
    }

    // Check rows
    const activeRows = getEffectiveSqlRows();
    if (sq.selectedRows.includes(3)) {
      setSpeech(
        'sql',
        '4행(도윤)의 score는 NULL이야! SQL에서 NULL은 숫자 조건(>= 80, >= 60)을 만족하지 않으니 금색 붓으로 4행을 빼 줘.',
        'wrong'
      );
      renderAll();
      return;
    }

    const sameRows =
      activeRows.length === lvl.targetRows.length &&
      activeRows.every((r, i) => r === lvl.targetRows[i]);

    if (!sameRows) {
      const targetNames = lvl.targetRows.map(r => `${r + 1}행(${SQL_ROWS[r].name})`).join(', ');
      setSpeech(
        'sql',
        `WHERE 조건 행이 맞지 않아! 2번 금색 붓으로 조건을 만족하는 [${targetNames}]만 정확히 칠해 봐.`,
        'wrong'
      );
      renderAll();
      return;
    }

    if (sq.orderDesc !== lvl.targetOrderDesc) {
      setSpeech(
        'sql',
        lvl.targetOrderDesc
          ? '점수가 높은 순서대로 정렬해야 해! 아래 툴벨트에서 [4. ORDER BY score DESC] 버튼을 켜 봐.'
          : '이 단계에서는 정렬(ORDER BY)을 켜지 않아도 돼!',
        'wrong'
      );
      renderAll();
      return;
    }

    if (sq.limitOne !== lvl.targetLimitOne) {
      setSpeech(
        'sql',
        lvl.targetLimitOne
          ? '1등 학생 딱 1명만 꺼내야 해! 아래 툴벨트에서 [5. LIMIT 1] 버튼을 켜 봐.'
          : '이 단계에서는 LIMIT 1을 켜지 말고 조건에 맞는 모든 행을 꺼내 봐!',
        'wrong'
      );
      renderAll();
      return;
    }

    state.cleared.sql[lvlIdx] = true;
    setSpeech(
      'sql',
      `🎉 정답 쿼리 통과! 파란 열(SELECT)과 금색 행(WHERE)이 교차한 초록색 칸들이 오른쪽 RESULT TABLE에 정확히 추출되었어!`,
      'good'
    );
    renderAll();
  }

  /* ==========================================================
     RENDERING
     ========================================================== */
  function renderAll() {
    const islandKey = state.island;
    const meta = ISLAND_META[islandKey];
    const lvlIdx = state.levelIndex[islandKey];
    const lvl = meta.levels[lvlIdx];
    const curState = state[islandKey];

    // 1. Update Top Island Tabs
    document.querySelectorAll('.island-demo-tab').forEach(btn => {
      const k = btn.getAttribute('data-island-tab');
      const isAct = k === islandKey;
      btn.classList.toggle('active', isAct);
      btn.setAttribute('aria-selected', isAct ? 'true' : 'false');
      const starsEl = btn.querySelector('.island-demo-tab-stars');
      if (starsEl && state.cleared[k]) {
        starsEl.textContent = state.cleared[k].map(done => (done ? '★' : '☆')).join('');
      }
    });

    // 2. Update HUD Header
    const idEl = document.getElementById('godot-stage-id');
    const nameEl = document.getElementById('godot-stage-name');
    const missionEl = document.getElementById('godot-mission-text');
    if (idEl) idEl.textContent = meta.stageId;
    if (nameEl) nameEl.textContent = meta.stageName;
    if (missionEl) missionEl.textContent = lvl.mission;

    // 3. Level Buttons
    const levelTabsEl = document.getElementById('godot-level-tabs');
    if (levelTabsEl) {
      levelTabsEl.innerHTML = meta.levels
        .map((l, idx) => {
          const isAct = idx === lvlIdx ? 'active' : '';
          const isDone = state.cleared[islandKey][idx] ? 'done' : '';
          return `<button type="button" class="godot-level-btn ${isAct} ${isDone}" data-level-idx="${idx}">${l.label}</button>`;
        })
        .join('');
      levelTabsEl.querySelectorAll('.godot-level-btn').forEach(b => {
        b.addEventListener('click', () => {
          const idx = parseInt(b.getAttribute('data-level-idx'), 10);
          switchLevel(islandKey, idx);
        });
      });
    }

    // 4. NPC Bar
    const npcAvatarEl = document.getElementById('godot-npc-avatar');
    const npcNameEl = document.getElementById('godot-npc-name');
    const npcSpeechEl = document.getElementById('godot-npc-speech');
    if (npcAvatarEl) npcAvatarEl.src = meta.npcAvatar;
    if (npcNameEl) npcNameEl.textContent = `[NPC · ${meta.npcName}]`;
    if (npcSpeechEl && curState) {
      npcSpeechEl.textContent = curState.speech;
      npcSpeechEl.className = 'godot-npc-speech ' + (curState.speechTone || '');
    }

    // 5. Field Background & Controls Guide
    const fieldEl = document.getElementById('godot-field');
    if (fieldEl) {
      fieldEl.style.backgroundImage = `url('${meta.bg}')`;
    }
    const guideEl = document.getElementById('godot-controls-guide');
    if (guideEl) {
      guideEl.innerHTML = meta.controlsHtml;
    }

    // 6. Render Island-Specific Board & Code Panel
    if (islandKey === 'ds') {
      renderDsBoard();
    } else if (islandKey === 'algo') {
      renderAlgoBoard();
    } else if (islandKey === 'sql') {
      renderSqlBoard();
    }
  }

  /* ---------- RENDER 1: DS (ST03 STACK) ---------- */
  function renderDsBoard() {
    const ds = state.ds;
    const lvlIdx = state.levelIndex.ds;
    const lvl = ISLAND_META.ds.levels[lvlIdx];
    const inner = document.getElementById('godot-field-inner');
    const codePanel = document.getElementById('godot-code-panel');
    if (!inner || !codePanel) return;

    const stackSlotsHtml = [];
    for (let i = 0; i < lvl.cap; i++) {
      const val = ds.stack[i];
      const isTop = i === ds.stack.length - 1 && val !== undefined;
      if (val !== undefined) {
        stackSlotsHtml.push(`
          <div class="st03-crate ${isTop ? 'is-top' : ''}">
            <span>[${i}] ${val}</span>
            ${isTop ? '<span class="st03-top-tag">TOP</span>' : ''}
          </div>
        `);
      } else {
        stackSlotsHtml.push(`
          <div style="width:116px;height:36px;border:2px dashed rgba(29,27,42,0.3);border-radius:6px;display:grid;place-items:center;font-size:11px;color:#6b4a2b;font-weight:700;">
            빈 슬롯 [${i}]
          </div>
        `);
      }
    }

    const railHtml =
      ds.incoming.length > 0
        ? ds.incoming
            .map(
              (item, idx) =>
                `<div class="st03-rail-crate ${idx === 0 ? 'first' : ''}" title="${idx === 0 ? '클릭하여 집기' : '대기 중'}">${item}</div>`
            )
            .join('')
        : `<span style="font-size:12px;color:#6b4a2b;font-weight:800;">모든 상자 반입 완료</span>`;

    const outSlotsHtml = lvl.target
      .map((tVal, idx) => {
        const filledVal = ds.output[idx];
        if (filledVal) {
          return `<div class="st03-out-slot filled">${filledVal} ✓</div>`;
        }
        return `<div class="st03-out-slot">목표: ${tVal}</div>`;
      })
      .join('<span style="font-weight:900;color:#6b4a2b;">→</span>');

    const heldBadgeHtml = ds.held
      ? `<div class="stage-robot-held">📦 ${ds.held}</div>`
      : '';

    inner.innerHTML = `
      <div class="st03-board">
        <!-- Station 1: Stack Tower -->
        <div class="st03-station st03-tower-spot ${ds.focusStation === 'tower' ? 'focused' : ''}" data-ds-station="tower">
          <div class="st03-station-title">
            <span>🏗️ 스택 타워 (CAP ${lvl.cap})</span>
            <span class="st03-key-hint">${ds.held ? 'E · PUSH' : 'E · POP'}</span>
          </div>
          <div class="st03-tower-slots">
            ${stackSlotsHtml.join('')}
          </div>
          <div style="margin-top:6px;font-size:11px;font-weight:800;color:#4a3b2c;text-align:center;">
            ${ds.held ? '클릭하여 맨 위에 쌓기 (Push)' : '클릭하여 맨 위 상자 꺼내기 (Pop)'}
          </div>
        </div>

        <!-- Station 2: Intake Rail -->
        <div class="st03-station st03-intake-spot ${ds.focusStation === 'intake' ? 'focused' : ''}" data-ds-station="intake">
          <div class="st03-station-title">
            <span>🚚 입고 레일 (입력)</span>
            <span class="st03-key-hint">E · 집기</span>
          </div>
          <div class="st03-rail-items">
            ${railHtml}
          </div>
          <div style="margin-top:4px;font-size:11px;font-weight:800;color:#4a3b2c;">
            남은 작업: [${ds.incoming.join(', ')}]
          </div>
        </div>

        <!-- Station 3: Peek Desk -->
        <div class="st03-station st03-desk-spot ${ds.focusStation === 'desk' ? 'focused' : ''}" data-ds-station="desk">
          <div class="st03-station-title">
            <span>🔍 Top 확인대</span>
            <span class="st03-key-hint">PEEK</span>
          </div>
          <div style="font-size:13px;font-weight:900;color:#1d1b2a;padding:6px 0;">
            ${ds.peeked ? `확인된 Top: <b style="color:#2f5fb3;font-size:16px;">${ds.lastPeekVal}</b> ✓` : '클릭하여 Top 확인'}
          </div>
          <div style="font-size:10.5px;color:#6b4a2b;font-weight:700;">
            ${lvl.requirePeek ? '★ 1단계 필수 미션' : '꺼내지 않고 맨 위 조회'}
          </div>
        </div>

        <!-- Station 4: Output Workbench -->
        <div class="st03-station st03-output-spot ${ds.focusStation === 'output' ? 'focused' : ''}" data-ds-station="output">
          <div class="st03-station-title">
            <span>🛠️ 복구 결과 작업대 (목표 순서: ${lvl.target.join(' → ')})</span>
            <span class="st03-key-hint">E · 등록</span>
          </div>
          <div class="st03-output-slots">
            ${outSlotsHtml}
          </div>
        </div>

        <!-- Walking Robot Actor -->
        <div class="stage-robot-actor" style="left:${ds.robotPos.left}; top:${ds.robotPos.top};">
          ${heldBadgeHtml}
          <img src="assets/robot.png" alt="작업 로봇">
          <span class="stage-robot-prompt">클릭 / E</span>
        </div>
      </div>
    `;

    inner.querySelectorAll('[data-ds-station]').forEach(el => {
      el.addEventListener('click', () => {
        interactDsStation(el.getAttribute('data-ds-station'));
      });
    });

    const topItem = ds.stack.length > 0 ? ds.stack[ds.stack.length - 1] : '비어 있음';
    codePanel.innerHTML = `
      <div class="godot-state-box">
        <div class="godot-box-header">
          <span>STACK STATUS · 실시간 상태</span>
          <span>LIFO (후입선출)</span>
        </div>
        <div class="godot-info-rows">
          <div class="godot-info-item"><span>현재 Top</span><b>${topItem}</b></div>
          <div class="godot-info-item"><span>적재 수량</span><b>${ds.stack.length} / ${lvl.cap}</b></div>
          <div class="godot-info-item"><span>로봇 손(Held)</span><b>${ds.held || '빈손'}</b></div>
          <div class="godot-info-item"><span>Peek 확인</span><b>${ds.peeked ? '완료 ✓' : lvl.requirePeek ? '필수!' : '선택'}</b></div>
        </div>
      </div>

      <div class="godot-live-code-box">
        <div class="godot-box-header">
          <span>LIVE PYTHON CODE · 실행 로그</span>
          <span>st03_stack.py</span>
        </div>
        <pre class="godot-code-pre">${ds.codeLogs.slice(-9).join('\n')}</pre>
      </div>
    `;
  }

  /* ---------- RENDER 2: ALGO (ALG01 SORTING) ---------- */
  function renderAlgoBoard() {
    const al = state.algo;
    const lvlIdx = state.levelIndex.algo;
    const lvl = ISLAND_META.algo.levels[lvlIdx];
    const inner = document.getElementById('godot-field-inner');
    const codePanel = document.getElementById('godot-code-panel');
    if (!inner || !codePanel) return;

    const n = al.arr.length;
    const isDone = state.cleared.algo[lvlIdx];

    // Determine crate highlights & robot X percent
    let robotIdx = 0;
    const cratesHtml = al.arr
      .map((val, idx) => {
        let boxClass = '';
        let tagHtml = '';

        if (al.mode === 'bubble') {
          const settledStart = n - al.passIdx;
          if (isDone || idx >= settledStart) {
            boxClass = 'settled';
            tagHtml = '<span class="alg01-status-tag settled">확정</span>';
          } else if (idx === al.cursor || idx === al.cursor + 1) {
            boxClass = 'comparing';
            tagHtml = `<span class="alg01-status-tag compare">${idx === al.cursor ? '왼쪽(j)' : '오른쪽(j+1)'}</span>`;
          }
          robotIdx = al.cursor + 0.5;
        } else if (al.mode === 'selection') {
          if (isDone || idx < al.sortedCount) {
            boxClass = 'settled';
            tagHtml = '<span class="alg01-status-tag settled">확정</span>';
          } else if (idx === al.selectedCrate) {
            boxClass = 'comparing';
            tagHtml = '<span class="alg01-status-tag compare">선택 후보</span>';
          } else {
            tagHtml = '<span class="alg01-status-tag" style="background:#36334d;color:#fff;">미정렬</span>';
          }
          robotIdx = Math.min(n - 1, Math.max(al.sortedCount, al.selectedCrate));
        } else if (al.mode === 'insertion') {
          if (al.liftedKey !== null && idx === al.holeIndex) {
            boxClass = 'hole';
            tagHtml = '<span class="alg01-status-tag compare">빈칸(Hole)</span>';
            robotIdx = al.holeIndex;
          } else if (isDone || idx < al.insIndex) {
            boxClass = 'settled';
            tagHtml = '<span class="alg01-status-tag settled">정렬 구간</span>';
          } else if (idx === al.insIndex && al.liftedKey === null) {
            boxClass = 'comparing';
            tagHtml = '<span class="alg01-status-tag compare">이번 카드(i)</span>';
            robotIdx = al.insIndex;
          }
        }

        const displayVal = al.mode === 'insertion' && al.liftedKey !== null && idx === al.holeIndex ? '빈칸' : val;

        return `
          <div class="alg01-crate-slot" data-crate-idx="${idx}">
            <span class="alg01-index-label">idx [${idx}]</span>
            <div class="alg01-crate-box ${boxClass}">${displayVal}</div>
            ${tagHtml}
          </div>
        `;
      })
      .join('');

    // Robot horizontal position
    const pct = Math.round(18 + (robotIdx / Math.max(1, n - 1)) * 64);
    const heldHtml =
      al.mode === 'insertion' && al.liftedKey !== null
        ? `<div class="stage-robot-held">🃏 key = ${al.liftedKey}</div>`
        : '';

    // Action buttons per sorting algorithm
    let actionsHtml = '';
    if (al.mode === 'bubble') {
      const a = al.arr[al.cursor];
      const b = al.arr[al.cursor + 1];
      actionsHtml = `
        <button type="button" class="alg01-station-btn primary" id="alg-btn-swap">
          [1] ⇄ 두 값 교환 (Swap ${a !== undefined ? `${a} ↔ ${b}` : ''})
        </button>
        <button type="button" class="alg01-station-btn" id="alg-btn-keep">
          [2] → 그대로 통과 (Keep)
        </button>
      `;
    } else if (al.mode === 'selection') {
      actionsHtml = `
        <div style="background:rgba(29,27,42,0.88);color:#f2c14e;padding:8px 16px;border-radius:8px;border:2px solid #f2c14e;font-size:13px;font-weight:800;">
          👆 위 상자들 중 미정렬 구간(idx ${Math.min(al.sortedCount, n - 1)}~${n - 1})에서 <b>가장 작은 숫자 상자</b>를 직접 클릭하세요!
        </div>
      `;
    } else if (al.mode === 'insertion') {
      actionsHtml = `
        <button type="button" class="alg01-station-btn ${al.liftedKey === null ? 'primary' : ''}" id="alg-btn-lift">
          [1] 🃏 새 카드 들기 (Lift)
        </button>
        <button type="button" class="alg01-station-btn ${al.liftedKey !== null ? 'primary' : ''}" id="alg-btn-shift">
          [2] ⇢ 큰 값 오른쪽 밀기 (Shift)
        </button>
        <button type="button" class="alg01-station-btn" id="alg-btn-insert" style="background:#bfe3b4;">
          [3] 📥 빈칸에 카드 꽂기 (Insert)
        </button>
      `;
    }

    inner.innerHTML = `
      <div class="alg01-board">
        <div class="alg01-algo-banner">${lvl.banner}</div>
        <div class="alg01-crates-row">
          ${cratesHtml}
        </div>
        <div class="stage-robot-actor" style="left:${pct}%; top:315px;">
          ${heldHtml}
          <img src="assets/robot.png" alt="정렬 로봇">
        </div>
        <div class="alg01-actions-bar">
          ${actionsHtml}
        </div>
      </div>
    `;

    // Bind crate click events
    inner.querySelectorAll('[data-crate-idx]').forEach(slot => {
      slot.addEventListener('click', () => {
        const idx = parseInt(slot.getAttribute('data-crate-idx'), 10);
        if (al.mode === 'selection') {
          algoSelectionPick(idx);
        } else if (al.mode === 'bubble') {
          const leftVal = al.arr[al.cursor];
          const rightVal = al.arr[al.cursor + 1];
          algoBubbleStep(leftVal > rightVal);
        } else if (al.mode === 'insertion') {
          if (al.liftedKey === null && idx === al.insIndex) {
            algoInsertionAction('lift');
          } else if (al.liftedKey !== null && idx === al.holeIndex - 1) {
            algoInsertionAction('shift');
          } else if (al.liftedKey !== null && idx === al.holeIndex) {
            algoInsertionAction('insert');
          }
        }
      });
    });

    const swapBtn = document.getElementById('alg-btn-swap');
    const keepBtn = document.getElementById('alg-btn-keep');
    if (swapBtn) swapBtn.addEventListener('click', () => algoBubbleStep(true));
    if (keepBtn) keepBtn.addEventListener('click', () => algoBubbleStep(false));

    const liftBtn = document.getElementById('alg-btn-lift');
    const shiftBtn = document.getElementById('alg-btn-shift');
    const insertBtn = document.getElementById('alg-btn-insert');
    if (liftBtn) liftBtn.addEventListener('click', () => algoInsertionAction('lift'));
    if (shiftBtn) shiftBtn.addEventListener('click', () => algoInsertionAction('shift'));
    if (insertBtn) insertBtn.addEventListener('click', () => algoInsertionAction('insert'));

    const sortedTarget = lvl.initial.slice().sort((x, y) => x - y);
    codePanel.innerHTML = `
      <div class="godot-state-box">
        <div class="godot-box-header">
          <span>SORTING METRICS · 정렬 계기판</span>
          <span>${al.mode.toUpperCase()} SORT</span>
        </div>
        <div class="godot-info-rows">
          <div class="godot-info-item"><span>비교 횟수 (cmp)</span><b>${al.comparisons}회</b></div>
          <div class="godot-info-item"><span>기록 횟수 (write)</span><b>${al.writes}회</b></div>
          <div class="godot-info-item"><span>현재 배열</span><b>[${al.arr.join(', ')}]</b></div>
          <div class="godot-info-item"><span>목표 배열</span><b>[${sortedTarget.join(', ')}]</b></div>
        </div>
      </div>

      <div class="godot-live-code-box">
        <div class="godot-box-header">
          <span>LIVE ALGORITHM TRACE · 실행 코드</span>
          <span>alg01_sort.py</span>
        </div>
        <pre class="godot-code-pre">${al.codeLines.slice(-9).join('\n')}</pre>
      </div>
    `;
  }

  /* ---------- RENDER 3: SQL (SQL01 5x5 DRAWER) ---------- */
  function renderSqlBoard() {
    const sq = state.sql;
    const inner = document.getElementById('godot-field-inner');
    const codePanel = document.getElementById('godot-code-panel');
    if (!inner || !codePanel) return;

    const effectiveRows = getEffectiveSqlRows();

    // Build 5x5 Grid Header Row
    let gridHtml = `<div style="font-size:10px;font-weight:900;color:#f2c14e;text-align:center;">행\\열</div>`;
    SQL_COLUMNS.forEach(col => {
      const orderIdx = sq.selectedCols.indexOf(col);
      const isSel = orderIdx >= 0;
      gridHtml += `
        <div class="sql01-col-header ${isSel ? 'selected' : ''}" data-sql-col="${col}" title="클릭하여 '${col}' 열 선택/해제">
          ${col}
          ${isSel ? `<span class="sql01-col-order-badge">${orderIdx + 1}</span>` : ''}
        </div>
      `;
    });

    // Build 5x5 Rows & Cells
    SQL_ROWS.forEach((rowObj, rIdx) => {
      const rowSelected = effectiveRows.includes(rIdx);
      gridHtml += `
        <div class="sql01-row-badge ${sq.selectedRows.includes(rIdx) ? 'pass' : ''}" data-sql-row="${rIdx}" title="클릭하여 ${rIdx + 1}행 WHERE 조건 토글" style="cursor:pointer;">
          R${rIdx + 1}
        </div>
      `;

      SQL_COLUMNS.forEach((col, cIdx) => {
        const val = rowObj[col];
        const isNull = val === null;
        const colSelected = sq.selectedCols.includes(col);
        const isHit = colSelected && rowSelected;

        let cellClass = '';
        if (isHit) cellClass = 'cell-hit';
        else if (colSelected) cellClass = 'cell-col';
        else if (sq.selectedRows.includes(rIdx)) cellClass = 'cell-row';

        if (isNull) cellClass += ' is-null';
        const isRobotHere = sq.cursorRow === rIdx && sq.cursorCol === cIdx;
        if (isRobotHere) cellClass += ' robot-here';

        gridHtml += `
          <div class="sql01-cell ${cellClass}" data-r="${rIdx}" data-c="${cIdx}">
            <span>${isNull ? 'NULL' : val}</span>
            ${isRobotHere ? `<img src="assets/robot.png" class="sql01-cell-robot" alt="로봇 커서">` : ''}
          </div>
        `;
      });
    });

    inner.innerHTML = `
      <div class="sql01-board">
        <div class="sql01-drawer-wrap">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;font-size:11.5px;font-weight:800;color:#f6e7c8;">
            <span>🗄️ students 테이블 (5×5 서랍장)</span>
            <span><b style="color:#5fd6ff;">파랑(SELECT 열)</b> × <b style="color:#f2c14e;">금색(WHERE 행)</b> = <b style="color:#9ef0b4;">초록(추출 결과)</b></span>
          </div>
          <div class="sql01-grid">
            ${gridHtml}
          </div>
        </div>

        <!-- Authentic SQL Tool Belt -->
        <div class="sql01-toolbelt">
          <button type="button" class="sql01-tool-btn ${sq.tool === 'select' ? 'active' : ''}" data-sql-tool="select">
            <img src="assets/sql_drawer/tool_blue_brush.png" alt="">
            <span>1 · 열 붓 (SELECT)</span>
          </button>
          <button type="button" class="sql01-tool-btn ${sq.tool === 'where' ? 'active' : ''}" data-sql-tool="where">
            <img src="assets/sql_drawer/tool_gold_brush.png" alt="">
            <span>2 · 조건 붓 (WHERE)</span>
          </button>
          <button type="button" class="sql01-tool-btn ${sq.tool === 'eraser' ? 'active' : ''}" data-sql-tool="eraser">
            <img src="assets/sql_drawer/tool_eraser.png" alt="">
            <span>3 · 지우개</span>
          </button>
          <button type="button" class="sql01-tool-btn ${sq.orderDesc ? 'active' : ''}" id="sql-toggle-order">
            <img src="assets/sql_drawer/tool_funnel.png" alt="">
            <span>4 · ORDER BY score DESC ${sq.orderDesc ? '✓' : ''}</span>
          </button>
          <button type="button" class="sql01-tool-btn ${sq.limitOne ? 'active' : ''}" id="sql-toggle-limit">
            <span>5 · LIMIT 1 ${sq.limitOne ? '✓' : ''}</span>
          </button>
          <button type="button" class="sql01-tool-btn submit-btn" id="sql-btn-submit">
            <img src="assets/sql_drawer/tool_submit.png" alt="">
            <span>Enter · 제출</span>
          </button>
        </div>
      </div>
    `;

    // Bind Grid Events
    inner.querySelectorAll('[data-sql-col]').forEach(el => {
      el.addEventListener('click', () => {
        toggleSqlColumn(el.getAttribute('data-sql-col'));
      });
    });

    inner.querySelectorAll('[data-sql-row]').forEach(el => {
      el.addEventListener('click', () => {
        toggleSqlRow(parseInt(el.getAttribute('data-sql-row'), 10));
      });
    });

    inner.querySelectorAll('.sql01-cell').forEach(el => {
      el.addEventListener('click', () => {
        const r = parseInt(el.getAttribute('data-r'), 10);
        const c = parseInt(el.getAttribute('data-c'), 10);
        paintSqlCell(r, c);
      });
    });

    inner.querySelectorAll('[data-sql-tool]').forEach(btn => {
      btn.addEventListener('click', () => {
        sq.tool = btn.getAttribute('data-sql-tool');
        renderAll();
      });
    });

    const orderBtn = document.getElementById('sql-toggle-order');
    const limitBtn = document.getElementById('sql-toggle-limit');
    const submitBtn = document.getElementById('sql-btn-submit');

    if (orderBtn) {
      orderBtn.addEventListener('click', () => {
        pushHistory('sql');
        sq.orderDesc = !sq.orderDesc;
        setSpeech('sql', `ORDER BY score DESC(점수 내림차순 정렬)를 ${sq.orderDesc ? '켰어!' : '껐어.'}`, '');
        renderAll();
      });
    }
    if (limitBtn) {
      limitBtn.addEventListener('click', () => {
        pushHistory('sql');
        sq.limitOne = !sq.limitOne;
        setSpeech('sql', `LIMIT 1(상위 1건만 추출) 옵션을 ${sq.limitOne ? '켰어!' : '껐어.'}`, '');
        renderAll();
      });
    }
    if (submitBtn) {
      submitBtn.addEventListener('click', submitSqlQuery);
    }

    // Build Live Result Table Preview
    let resultRows = effectiveRows.map(idx => SQL_ROWS[idx]);
    if (sq.orderDesc) {
      resultRows.sort((a, b) => {
        if (a.score === null) return 1;
        if (b.score === null) return -1;
        return b.score - a.score;
      });
    }
    if (sq.limitOne) {
      resultRows = resultRows.slice(0, 1);
    }

    let tableHtml = '';
    if (sq.selectedCols.length === 0) {
      tableHtml = `<div style="font-size:12px;color:#8d98ab;padding:8px 0;">파란 붓(SELECT)으로 가져올 열을 칠하면 실시간 결과 테이블이 여기에 표시됩니다.</div>`;
    } else {
      const ths = sq.selectedCols.map(c => `<th>${c}</th>`).join('');
      const trs =
        resultRows.length > 0
          ? resultRows
              .map(r => {
                const tds = sq.selectedCols
                  .map(c => `<td>${r[c] === null ? '<i style="color:#888">NULL</i>' : r[c]}</td>`)
                  .join('');
                return `<tr>${tds}</tr>`;
              })
              .join('')
          : `<tr><td colspan="${sq.selectedCols.length}" style="text-align:center;color:#888;">선택된 행 없음</td></tr>`;
      tableHtml = `
        <table class="sql-result-table">
          <thead><tr>${ths}</tr></thead>
          <tbody>${trs}</tbody>
        </table>
      `;
    }

    codePanel.innerHTML = `
      <div class="godot-live-code-box" style="flex:0 0 auto;">
        <div class="godot-box-header">
          <span>LIVE SQL QUERY · 실시간 생성 쿼리</span>
          <span>sql01_drawer.sql</span>
        </div>
        <pre class="godot-code-pre">${buildLiveSqlText()}</pre>
      </div>

      <div class="sql-result-preview" style="flex:1;">
        <div class="godot-box-header">
          <span>RESULT TABLE · 추출 미리보기 (${sq.selectedCols.length > 0 ? resultRows.length : 0}건)</span>
          <span>초록 교차 칸(R×C)</span>
        </div>
        ${tableHtml}
      </div>
    `;
  }

  /* -------------------- NAVIGATION & CONTROLS -------------------- */
  function switchIsland(islandKey) {
    if (!ISLAND_META[islandKey]) return;
    state.island = islandKey;
    renderAll();
  }

  function switchLevel(islandKey, idx) {
    const meta = ISLAND_META[islandKey];
    if (!meta || idx < 0 || idx >= meta.levels.length) return;
    state.levelIndex[islandKey] = idx;
    if (islandKey === 'ds') initDsLevel(idx);
    else if (islandKey === 'algo') initAlgoLevel(idx);
    else if (islandKey === 'sql') initSqlLevel(idx);
    renderAll();
  }

  function showHintCurrent() {
    const islandKey = state.island;
    const lvlIdx = state.levelIndex[islandKey];
    const lvl = ISLAND_META[islandKey].levels[lvlIdx];
    setSpeech(islandKey, lvl.hint, 'good');
    renderAll();
  }

  function resetCurrent() {
    switchLevel(state.island, state.levelIndex[state.island]);
  }

  function nextLevelOrIsland() {
    const islandKey = state.island;
    const curIdx = state.levelIndex[islandKey];
    const total = ISLAND_META[islandKey].levels.length;
    if (curIdx + 1 < total) {
      switchLevel(islandKey, curIdx + 1);
    } else {
      const order = ['ds', 'algo', 'sql'];
      const nextIsland = order[(order.indexOf(islandKey) + 1) % order.length];
      switchIsland(nextIsland);
    }
  }

  /* -------------------- KEYBOARD HANDLER -------------------- */
  function handleKeyDown(e) {
    const tag = (e.target && e.target.tagName) || '';
    if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return;

    const demoSection = document.getElementById('demo');
    if (!demoSection) return;
    const rect = demoSection.getBoundingClientRect();
    // Only capture game keys when #demo section is visible in viewport
    if (rect.bottom < 80 || rect.top > window.innerHeight - 80) return;

    const key = e.key.toLowerCase();

    if (key === 'z') {
      e.preventDefault();
      undoCurrent();
      return;
    }
    if (key === 'r') {
      e.preventDefault();
      resetCurrent();
      return;
    }
    if (key === 'f') {
      e.preventDefault();
      showHintCurrent();
      return;
    }

    if (state.island === 'ds') {
      const ds = state.ds;
      const order = ['tower', 'desk', 'intake', 'output'];
      if (['a', 'arrowleft'].includes(key)) {
        e.preventDefault();
        ds.focusStation = 'tower';
        ds.robotPos = DS_STATION_POS.tower;
        renderAll();
      } else if (['d', 'arrowright'].includes(key)) {
        e.preventDefault();
        ds.focusStation = 'intake';
        ds.robotPos = DS_STATION_POS.intake;
        renderAll();
      } else if (['w', 'arrowup'].includes(key)) {
        e.preventDefault();
        ds.focusStation = 'desk';
        ds.robotPos = DS_STATION_POS.desk;
        renderAll();
      } else if (['s', 'arrowdown'].includes(key)) {
        e.preventDefault();
        ds.focusStation = 'output';
        ds.robotPos = DS_STATION_POS.output;
        renderAll();
      } else if (key === 'e' || key === ' ') {
        e.preventDefault();
        interactDsStation(ds.focusStation || order[0]);
      }
    } else if (state.island === 'algo') {
      const al = state.algo;
      if (al.mode === 'bubble') {
        if (key === '1') {
          e.preventDefault();
          algoBubbleStep(true);
        } else if (key === '2') {
          e.preventDefault();
          algoBubbleStep(false);
        } else if (key === 'e') {
          e.preventDefault();
          algoBubbleStep(al.arr[al.cursor] > al.arr[al.cursor + 1]);
        }
      } else if (al.mode === 'selection') {
        if (['a', 'arrowleft'].includes(key)) {
          e.preventDefault();
          al.selectedCrate = Math.max(al.sortedCount, al.selectedCrate - 1);
          renderAll();
        } else if (['d', 'arrowright'].includes(key)) {
          e.preventDefault();
          al.selectedCrate = Math.min(al.arr.length - 1, al.selectedCrate + 1);
          renderAll();
        } else if (key === 'e' || key === '1') {
          e.preventDefault();
          algoSelectionPick(al.selectedCrate);
        }
      } else if (al.mode === 'insertion') {
        if (key === '1') {
          e.preventDefault();
          algoInsertionAction('lift');
        } else if (key === '2') {
          e.preventDefault();
          algoInsertionAction('shift');
        } else if (key === '3') {
          e.preventDefault();
          algoInsertionAction('insert');
        }
      }
    } else if (state.island === 'sql') {
      const sq = state.sql;
      if (['w', 'arrowup'].includes(key)) {
        e.preventDefault();
        sq.cursorRow = Math.max(0, sq.cursorRow - 1);
        renderAll();
      } else if (['s', 'arrowdown'].includes(key)) {
        e.preventDefault();
        sq.cursorRow = Math.min(4, sq.cursorRow + 1);
        renderAll();
      } else if (['a', 'arrowleft'].includes(key)) {
        e.preventDefault();
        sq.cursorCol = Math.max(0, sq.cursorCol - 1);
        renderAll();
      } else if (['d', 'arrowright'].includes(key)) {
        e.preventDefault();
        sq.cursorCol = Math.min(4, sq.cursorCol + 1);
        renderAll();
      } else if (key === 'e' || key === ' ') {
        e.preventDefault();
        paintSqlCell(sq.cursorRow, sq.cursorCol);
      } else if (key === '1') {
        sq.tool = 'select';
        renderAll();
      } else if (key === '2') {
        sq.tool = 'where';
        renderAll();
      } else if (key === '3') {
        sq.tool = 'eraser';
        renderAll();
      } else if (key === '4') {
        pushHistory('sql');
        sq.orderDesc = !sq.orderDesc;
        renderAll();
      } else if (key === '5') {
        pushHistory('sql');
        sq.limitOne = !sq.limitOne;
        renderAll();
      } else if (key === 'enter') {
        e.preventDefault();
        submitSqlQuery();
      }
    }
  }

  /* -------------------- BOOTSTRAP -------------------- */
  function init() {
    initDsLevel(0);
    initAlgoLevel(0);
    initSqlLevel(0);

    document.querySelectorAll('.island-demo-tab').forEach(btn => {
      btn.addEventListener('click', () => {
        switchIsland(btn.getAttribute('data-island-tab'));
      });
    });

    const btnUndo = document.getElementById('godot-btn-undo');
    const btnHint = document.getElementById('godot-btn-hint');
    const btnReset = document.getElementById('godot-btn-reset');
    const btnNext = document.getElementById('godot-btn-next');

    if (btnUndo) btnUndo.addEventListener('click', undoCurrent);
    if (btnHint) btnHint.addEventListener('click', showHintCurrent);
    if (btnReset) btnReset.addEventListener('click', resetCurrent);
    if (btnNext) btnNext.addEventListener('click', nextLevelOrIsland);

    window.addEventListener('keydown', handleKeyDown);

    try {
      const params = new URLSearchParams(window.location.search);
      const tab = params.get('tab');
      const lvl = parseInt(params.get('level') || '0', 10);
      const preview = params.get('preview') === '1';
      if (tab && ISLAND_META[tab]) {
        state.island = tab;
        if (lvl >= 0 && lvl < 3) {
          switchLevel(tab, lvl);
        }
        setTimeout(() => {
          const demoEl = document.getElementById('demo');
          if (demoEl) demoEl.scrollIntoView({ behavior: 'instant', block: 'start' });
        }, 50);
      }
      if (preview) {
        document.querySelectorAll('main > section:not(#demo), header').forEach(el => {
          el.style.display = 'none';
        });
        const demoSec = document.getElementById('demo');
        if (demoSec) demoSec.style.padding = '24px 4%';
        if (state.island === 'ds') {
          interactDsStation('intake');
          interactDsStation('tower');
          interactDsStation('intake');
          interactDsStation('tower');
          interactDsStation('desk');
        } else if (state.island === 'algo') {
          if (state.levelIndex.algo === 0) {
            algoBubbleStep(true);
          }
        } else if (state.island === 'sql') {
          switchLevel('sql', 1);
          toggleSqlColumn('name');
          toggleSqlColumn('score');
          toggleSqlRow(0);
          toggleSqlRow(2);
        }
      }
    } catch (_) {}

    renderAll();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
