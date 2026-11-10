(function() {
  const LEVELS = [
    {
      arr: [10, 30, 40, null, null],
      tray: 20,
      target: [10, 20, 30, 40],
      goal: "인덱스 1에 20 넣기 (뒤쪽 상자부터 한 칸씩 뒤로 밀어 자리를 만드세요)",
      hint: "40번을 3번 칸으로, 30번을 2번 칸으로 밀고, 입고 트레이의 20을 1번 칸에 넣으세요!",
      opt: 3
    },
    {
      arr: [10, 20, 30, 40, null],
      tray: null,
      target: [20, 30, 40],
      goal: "인덱스 0의 10을 반환 레버로 버리고 빈칸 없이 왼쪽으로 당기기",
      hint: "0번 칸의 10을 집어 반환 레버에 넣고, 20, 30, 40을 왼쪽으로 차례차례 당기세요!",
      opt: 4
    }
  ];

  let currentLevelIdx = 0;
  let slots = [];
  let tray = null;
  let hand = null; // { v: value, from: slotIndex | 'tray' }
  let moves = 0;
  let mistakes = 0;
  let undoStack = [];
  let codeLog = [];
  let isDone = false;

  // DOM Elements
  const levelBadge = document.getElementById('demo-level-badge');
  const movesEl = document.getElementById('demo-moves');
  const mistakesEl = document.getElementById('demo-mistakes');
  const goalEl = document.getElementById('demo-goal');
  const speechEl = document.getElementById('demo-speech');
  const slotsContainer = document.getElementById('demo-slots');
  const trayCard = document.getElementById('demo-tray');
  const trayValueEl = document.getElementById('demo-tray-val');
  const binCard = document.getElementById('demo-bin');
  const handValueEl = document.getElementById('demo-hand-val');
  const codeContentEl = document.getElementById('demo-code-content');
  const telemetryLogEl = document.getElementById('demo-telemetry-log');
  const clearOverlay = document.getElementById('demo-clear-overlay');
  const clearDescEl = document.getElementById('demo-clear-desc');
  const nextBtn = document.getElementById('demo-next-btn');

  function initLevel(lvlIdx) {
    currentLevelIdx = lvlIdx % LEVELS.length;
    const L = LEVELS[currentLevelIdx];
    slots = [...L.arr];
    tray = L.tray;
    hand = null;
    moves = 0;
    mistakes = 0;
    undoStack = [];
    codeLog = [];
    isDone = false;

    clearOverlay.style.display = 'none';
    levelBadge.textContent = `레벨 0${currentLevelIdx + 1} / 0${LEVELS.length}`;
    goalEl.innerHTML = `<span>목표:</span> ${L.goal}`;
    speechEl.textContent = L.hint;
    
    emitTelemetry('problem_started', { level: currentLevelIdx + 1, goal: L.goal });
    render();
  }

  function snapshot() {
    undoStack.push({
      slots: [...slots],
      tray: tray,
      hand: hand ? { ...hand } : null,
      moves: moves,
      mistakes: mistakes,
      codeLog: [...codeLog]
    });
  }

  function undo() {
    if (isDone || undoStack.length === 0) return;
    const prev = undoStack.pop();
    slots = prev.slots;
    tray = prev.tray;
    hand = prev.hand;
    moves = prev.moves;
    mistakes = prev.mistakes;
    codeLog = prev.codeLog;
    speechEl.textContent = "한 걸음 되돌렸습니다.";
    render();
  }

  function emitTelemetry(eventType, details) {
    const timeStr = new Date().toTimeString().split(' ')[0];
    const detailStr = JSON.stringify(details);
    telemetryLogEl.innerHTML = `[${timeStr}] <span style="color:#34d399">POST /v1/events</span> event_type="<b>${eventType}</b>" ➔ <span style="color:#38bdf8">202 Accepted</span>`;
  }

  // Interaction: Slot Click
  function handleSlotClick(i) {
    if (isDone) return;

    // 1. Pick up crate from slot
    if (!hand) {
      if (slots[i] === null) {
        speechEl.textContent = `✗ ${i}번 칸은 비어 있습니다. 상자가 있는 칸을 클릭하세요.`;
        return;
      }
      snapshot();
      hand = { v: slots[i], from: i };
      slots[i] = null;
      codeLog.push({ code: `temp = arr[${i}];`, cmt: `${hand.v} 집기` });
      speechEl.textContent = `${i}번 칸의 상자 [${hand.v}]를 집었습니다. 바로 옆 빈칸에 놓아보세요.`;
      render();
      return;
    }

    // 2. Put down crate into slot
    if (slots[i] !== null) {
      mistakes++;
      speechEl.textContent = `✗ ${i}번 칸에는 이미 상자 [${slots[i]}]가 있습니다!`;
      render();
      return;
    }

    // Check adjacent move rule if from another slot
    if (typeof hand.from === 'number' && Math.abs(hand.from - i) > 1) {
      mistakes++;
      speechEl.textContent = `✗ 상자는 바로 옆 칸(±1)으로만 이동할 수 있습니다!`;
      render();
      return;
    }

    snapshot();
    slots[i] = hand.v;
    if (hand.from === 'tray') {
      codeLog.push({ code: `arr[${i}] = temp;`, cmt: `인덱스 ${i}에 새 상자 ${hand.v} 삽입!` });
      moves++;
      emitTelemetry('operation', { op: 'insert', slot: i, value: hand.v, moves: moves });
    } else if (hand.from === i) {
      codeLog.pop(); // Placed back where it came from
    } else {
      codeLog.push({ code: `arr[${i}] = arr[${hand.from}];`, cmt: `${hand.v}을 ${hand.from}번 ➔ ${i}번으로 이동` });
      moves++;
      emitTelemetry('operation', { op: 'shift', from: hand.from, to: i, value: hand.v, moves: moves });
    }

    hand = null;
    speechEl.textContent = `상자를 ${i}번 칸에 내려놓았습니다.`;
    checkWinCondition();
    render();
  }

  // Interaction: Tray Click
  function handleTrayClick() {
    if (isDone) return;
    if (!hand && tray !== null) {
      snapshot();
      hand = { v: tray, from: 'tray' };
      tray = null;
      codeLog.push({ code: `temp = ${hand.v};`, cmt: `입고 트레이에서 새 상자 꺼냄` });
      speechEl.textContent = `입고 트레이에서 상자 [${hand.v}]를 집었습니다. 배열의 빈칸에 놓아주세요.`;
      render();
    } else if (hand && hand.from === 'tray') {
      snapshot();
      tray = hand.v;
      hand = null;
      codeLog.pop();
      speechEl.textContent = `새 상자를 트레이로 되돌려놓았습니다.`;
      render();
    } else if (hand) {
      speechEl.textContent = `✗ 기존 배열 상자는 입고 트레이에 넣을 수 없습니다.`;
    }
  }

  // Interaction: Bin (Return/Delete) Click
  function handleBinClick() {
    if (isDone) return;
    if (!hand) {
      speechEl.textContent = `먼저 지우고 싶은 상자를 집어 오세요.`;
      return;
    }
    if (hand.from === 'tray') {
      speechEl.textContent = `✗ 새 상자는 버리지 말고 배열에 삽입해야 합니다!`;
      return;
    }
    const L = LEVELS[currentLevelIdx];
    if (L.target.includes(hand.v)) {
      mistakes++;
      speechEl.textContent = `✗ [${hand.v}]은(는) 최종 목표에 남아있어야 하는 상자입니다!`;
      render();
      return;
    }

    snapshot();
    moves++;
    codeLog.push({ code: `arr[${hand.from}] = null;`, cmt: `${hand.v} 삭제 완료` });
    emitTelemetry('operation', { op: 'delete', value: hand.v, moves: moves });
    speechEl.textContent = `상자 [${hand.v}]를 삭제했습니다! 이제 뒤쪽 상자들을 앞으로 당겨 빈틈을 채우세요.`;
    hand = null;
    checkWinCondition();
    render();
  }

  function checkWinCondition() {
    if (hand !== null) return;
    const L = LEVELS[currentLevelIdx];
    const currentItems = [];
    let hasGap = false;

    for (let v of slots) {
      if (v === null) {
        hasGap = true;
      } else if (hasGap) {
        // Gap exists before an item -> invalid array
        return;
      } else {
        currentItems.push(v);
      }
    }

    if (JSON.stringify(currentItems) === JSON.stringify(L.target)) {
      isDone = true;
      const stars = mistakes === 0 ? 3 : (mistakes <= 2 ? 2 : 1);
      clearDescEl.innerHTML = `배열 <b>[${currentItems.join(', ')}]</b> 완성!<br>이동 ${moves}회 (최적 ${L.opt}회) · 실수 ${mistakes}회<br>★ ${'★'.repeat(stars)}${'☆'.repeat(3 - stars)}`;
      clearOverlay.style.display = 'flex';
      emitTelemetry('attempt_succeeded', { level: currentLevelIdx + 1, moves: moves, mistakes: mistakes, stars: stars });
    }
  }

  function render() {
    movesEl.textContent = moves;
    mistakesEl.textContent = mistakes;

    // Render Slots
    slotsContainer.innerHTML = '';
    slots.forEach((val, idx) => {
      const slotBox = document.createElement('div');
      slotBox.className = 'slot-box' + (hand && hand.from === idx ? ' selected' : '');
      slotBox.onclick = () => handleSlotClick(idx);

      const idxLabel = document.createElement('span');
      idxLabel.className = 'slot-idx';
      idxLabel.textContent = `[${idx}]`;
      slotBox.appendChild(idxLabel);

      if (val !== null) {
        const crate = document.createElement('div');
        crate.className = 'crate';
        crate.textContent = val;
        slotBox.appendChild(crate);
      } else {
        const emptyLbl = document.createElement('span');
        emptyLbl.className = 'empty-slot-label';
        emptyLbl.textContent = '빈 칸';
        slotBox.appendChild(emptyLbl);
      }
      slotsContainer.appendChild(slotBox);
    });

    // Render Tray
    if (tray !== null) {
      trayValueEl.innerHTML = `<div class="crate tray-crate" style="width:70px; height:34px; font-size:14px;">${tray}</div>`;
      trayCard.style.opacity = '1';
    } else {
      trayValueEl.textContent = '(비어 있음)';
      trayCard.style.opacity = '0.6';
    }

    // Render Hand
    if (hand !== null) {
      handValueEl.innerHTML = `<div class="crate" style="width:70px; height:34px; font-size:14px; background:linear-gradient(135deg, #10b981, #059669); border-color:#a7f3d0;">${hand.v}</div>`;
    } else {
      handValueEl.textContent = '(비어 있음)';
    }

    // Render Code Panel
    const curArrStr = slots.map(x => x === null ? '_' : x).join(', ');
    let codeText = `<span class="code-kw">arr</span> = [${curArrStr}]\n`;
    codeText += `<span class="code-kw">length</span> = ${slots.filter(x => x !== null).length}\n`;
    if (hand) {
      codeText += `<span class="code-var">temp</span> = ${hand.v}  <span class="code-cmt">// 로봇이 든 상자</span>\n`;
    }
    codeText += `\n<span class="code-cmt">// ── 동작 로그 ──</span>\n`;
    if (codeLog.length === 0) {
      codeText += `<span class="code-cmt">// 상자를 조작하면 코드가 실시간 생성됩니다.</span>`;
    } else {
      codeLog.forEach((item, i) => {
        const isLast = i === codeLog.length - 1;
        const line = `${item.code}  <span class="code-cmt">// ${item.cmt}</span>\n`;
        codeText += isLast ? `<span class="code-hl">${line}</span>` : line;
      });
    }
    codeContentEl.innerHTML = codeText;
  }

  // Event Listeners
  trayCard.onclick = handleTrayClick;
  binCard.onclick = handleBinClick;
  document.getElementById('demo-undo-btn').onclick = undo;
  document.getElementById('demo-reset-btn').onclick = () => initLevel(currentLevelIdx);
  nextBtn.onclick = () => initLevel(currentLevelIdx + 1);

  // Keyboard Shortcuts: Z (undo), R (reset)
  window.addEventListener('keydown', (e) => {
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
    if (e.key === 'z' || e.key === 'Z') undo();
    if (e.key === 'r' || e.key === 'R') initLevel(currentLevelIdx);
  });

  // Start on load
  initLevel(0);
})();
