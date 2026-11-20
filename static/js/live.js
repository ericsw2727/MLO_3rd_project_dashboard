/* /staff/live/ — polls the admin live APIs every 3 seconds. */
(function () {
  'use strict';
  var config = JSON.parse(document.getElementById('live-config').textContent);
  var POLL_MS = 3000;
  var status = document.getElementById('live-status');
  var statusText = document.getElementById('live-status-text');
  var AREA_LABELS = { structures: '자료구조', algorithms: '알고리즘', sql: 'SQL', data: '데이터 탐색', unmapped: '미분류' };

  function $(id) { return document.getElementById(id); }
  function esc(value) {
    return String(value == null ? '' : value).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }
  function pct(value) { return value == null ? '—' : Math.round(value * 1000) / 10 + '%'; }
  function time(iso) {
    if (!iso) return '—';
    var d = new Date(iso);
    return isNaN(d) ? esc(iso) : d.toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' });
  }
  function get(url) {
    return fetch(url, { credentials: 'same-origin', headers: { Accept: 'application/json' } }).then(function (r) {
      if (r.status === 401 || r.status === 403) { window.location.href = '/staff/login/'; throw new Error('auth'); }
      if (!r.ok) throw new Error('HTTP ' + r.status);
      return r.json();
    });
  }
  function bars(el, items) {
    var max = Math.max.apply(null, items.map(function (i) { return i.value; }).concat([1]));
    el.innerHTML = items.length ? items.map(function (i) {
      return '<div class="bar-row"><span>' + esc(i.label) + '</span><div class="bar-track"><i style="width:' +
        Math.round(100 * i.value / max) + '%"></i></div><strong>' + esc(i.text != null ? i.text : i.value) + '</strong></div>';
    }).join('') : '<p class="empty">데이터 없음</p>';
  }
  function sparkline(points) {
    var w = 120, h = 26;
    var valid = points.filter(function (p) { return p != null; });
    if (!valid.length) return '<span class="muted">—</span>';
    var step = points.length > 1 ? w / (points.length - 1) : w;
    var d = '', pen = false;
    points.forEach(function (p, i) {
      if (p == null) { pen = false; return; }
      d += (pen ? 'L' : 'M') + (i * step).toFixed(1) + ',' + (h - p * (h - 2) - 1).toFixed(1);
      pen = true;
    });
    return '<svg class="spark" viewBox="0 0 ' + w + ' ' + h + '" width="' + w + '" height="' + h + '" aria-hidden="true">' +
      '<path d="' + d + '" fill="none" stroke="currentColor" stroke-width="1.6"/></svg>';
  }
  function setStatus(summary, error) {
    status.classList.toggle('stale', !!(error || (summary && summary.stale)));
    if (error) { statusText.textContent = '불러오기 실패: ' + error.message + ' (다시 시도 중)'; return; }
    if (summary.stale) {
      statusText.textContent = '수집 지연 — 마지막 갱신 ' + (summary.updated_at ? time(summary.updated_at) + ' (' + Math.round(summary.age_seconds) + '초 전)' : '기록 없음');
    } else {
      statusText.textContent = '실시간 수집 정상 · ' + time(summary.updated_at) + ' 갱신';
    }
  }

  function renderLive(summary, games, alerts) {
    $('kpi-events').textContent = summary.events_last_1m;
    $('kpi-sessions').textContent = summary.active_sessions_5m;
    $('kpi-alerts').textContent = alerts.alerts.length;
    var minutes = [];
    var now = Date.now();
    for (var m = games.minutes; m >= 1; m--) minutes.push(Math.floor((now - m * 60000) / 60000));
    var byGame = {};
    games.rows.forEach(function (row) {
      var g = byGame[row.minigame_id] || (byGame[row.minigame_id] = { attempts: 0, successes: 0, slots: {} });
      g.attempts += row.attempts || 0;
      g.successes += row.successes || 0;
      g.slots[Math.floor(new Date(row.window_start).getTime() / 60000)] = row.attempts ? row.successes / row.attempts : null;
    });
    var total = 0;
    var rows = games.games.map(function (game) {
      var g = byGame[game.minigame_id] || { attempts: 0, successes: 0, slots: {} };
      total += g.attempts;
      return { game: game, g: g };
    }).sort(function (a, b) { return b.g.attempts - a.g.attempts; });
    $('kpi-attempts').textContent = total;
    $('game-rows').innerHTML = rows.map(function (r) {
      var rate = r.g.attempts ? r.g.successes / r.g.attempts : null;
      return '<tr><td><strong>' + esc(r.game.minigame_id) + '</strong><small>' + esc(r.game.title) + '</small></td><td>' +
        esc(AREA_LABELS[r.game.area]) + '</td><td class="spark-cell">' +
        sparkline(minutes.map(function (k) { return r.g.slots[k] != null ? r.g.slots[k] : null; })) +
        '</td><td class="numeric">' + r.g.attempts + '</td><td class="numeric' + (rate != null && rate < 0.5 ? ' low' : '') + '">' + pct(rate) + '</td></tr>';
    }).join('');
    var note = $('mismatch-note');
    note.hidden = !games.category_mismatches.length;
    note.textContent = '게임이 보낸 category가 서버 카탈로그 영역과 다릅니다 (게임 파트에 알려 주세요): ' + games.category_mismatches.join(', ');
    bars($('area-bars'), games.areas.map(function (a) { return { label: a.label, value: a.attempts }; }));
    $('alert-rows').innerHTML = alerts.alerts.length ? alerts.alerts.map(function (a) {
      return '<tr><td>' + time(a.window_start) + '</td><td><strong>' + esc(a.minigame_id) + '</strong><small>' + esc(a.title || '카탈로그에 없음') +
        '</small></td><td>' + esc(a.area_label) + '</td><td class="numeric">' + esc(a.attempts) + '</td><td class="numeric">' + esc(a.failures) +
        '</td><td class="numeric low">' + pct(a.failure_rate) + '</td><td class="numeric">' + pct(a.baseline_rate) + '</td></tr>';
    }).join('') : '<tr><td colspan="7" class="empty">최근 60분 동안 실패 급증 경고가 없습니다.</td></tr>';
  }

  function renderUpdates(data) {
    var a = data.active;
    $('kpi-build').textContent = a.build_version ? pct(a.build_share) : '—';
    $('kpi-build-label').textContent = a.build_version ? 'EXE ' + a.build_version : '활성 릴리스 없음';
    $('kpi-content').textContent = pct(a.content_share);
    $('kpi-content-label').textContent = '팩 ' + a.content_version;
    $('kpi-below').textContent = a.min_build ? a.installs_below_min_build : '—';
    $('kpi-response').textContent = pct(data.prompt_response.rate);
    $('kpi-response-label').textContent = data.prompt_response.accepted + ' / ' + data.prompt_response.prompted + ' · 최근 ' + data.minutes + '분';
    var warn = $('pack-warning');
    warn.hidden = !data.pack_warning.review;
    warn.innerHTML = '⚠ 최근 15분 팩 다운로드 ' + data.pack_warning.downloads_15m + '건 중 실패율 ' + pct(data.pack_warning.failure_rate_15m) +
      ' — <a href="' + esc(config.releasesUrl) + '">팩 비활성화 검토</a> (자동으로 끄지 않습니다)';
    $('update-rows').innerHTML = data.windows.length ? data.windows.slice().reverse().map(function (w) {
      return '<tr><td>' + time(w.window_start) + '</td><td>' + esc(w.target_version) + '</td><td class="numeric">' + esc(w.downloads_started) +
        '</td><td class="numeric">' + esc(w.downloads_succeeded) + '</td><td class="numeric">' + esc(w.downloads_failed) + '</td><td class="numeric">' +
        esc(w.mounted) + '</td><td class="numeric' + (w.failure_rate >= 0.2 ? ' low' : '') + '">' + pct(w.failure_rate) + '</td><td class="numeric">' +
        (w.p50_duration_ms != null ? (w.p50_duration_ms / 1000).toFixed(1) + '초' : '—') + '</td></tr>';
    }).join('') : '<tr><td colspan="8" class="empty">최근 ' + data.minutes + '분 동안 업데이트 이벤트가 없습니다.</td></tr>';
    bars($('reason-bars'), data.failure_reasons.map(function (r) { return { label: r.reason, value: r.count }; }));
    function versionBars(kind, active) {
      return data.versions.filter(function (v) { return v.kind === kind; })
        .sort(function (x, y) { return y.installs - x.installs; })
        .map(function (v) { return { label: v.version + (v.version === active ? ' (현재)' : ''), value: v.installs, text: v.installs + ' · ' + pct(v.share) }; });
    }
    bars($('build-bars'), versionBars('build', a.build_version));
    bars($('content-bars'), versionBars('content', a.content_version));
  }

  function tick() {
    var requests = config.tab === 'updates'
      ? [get('/api/admin/live/summary'), get('/api/admin/live/updates?minutes=60')]
      : [get('/api/admin/live/summary'), get('/api/admin/live/minigames?minutes=30'), get('/api/admin/live/alerts?minutes=60')];
    Promise.all(requests).then(function (r) {
      setStatus(r[0]);
      if (config.tab === 'updates') renderUpdates(r[1]); else renderLive(r[0], r[1], r[2]);
    }).catch(function (e) { if (e.message !== 'auth') setStatus(null, e); })
      .then(function () { setTimeout(tick, document.hidden ? POLL_MS * 5 : POLL_MS); });
  }
  tick();
})();
