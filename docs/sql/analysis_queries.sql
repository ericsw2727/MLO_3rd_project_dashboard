-- Read-only analysis examples. MySQL 8+, UTC timestamps.
-- Change these example boundaries and source as needed.
SET @window_start = '2026-11-01 00:00:00';
SET @window_end = '2026-11-06 00:00:00';
SET @source = 'demo';

-- Per-player behavior counts; LEFT JOIN preserves players without logs.
SELECT p.id AS player_id, p.display_name, p.source,
 COUNT(e.id) AS event_count,
 COALESCE(SUM(e.event_type IN ('success', 'operation_succeeded')), 0) AS successes,
 COALESCE(SUM(e.event_type IN ('failure', 'operation_failed')), 0) AS failures,
 COALESCE(SUM(e.event_type = 'hint'), 0) AS hints,
 ROUND(100.0 * SUM(e.event_type IN ('success', 'operation_succeeded')) /
 NULLIF(SUM(e.event_type IN ('success', 'failure', 'operation_succeeded', 'operation_failed')), 0), 1) AS success_rate
FROM telemetry_player p
LEFT JOIN telemetry_playsession s ON s.player_id = p.id
LEFT JOIN telemetry_behaviorevent e ON e.session_id = s.id
 AND e.occurred_at >= @window_start AND e.occurred_at < @window_end
WHERE p.source = @source
GROUP BY p.id, p.display_name, p.source;

-- Session summary separately: do not multiply session rows by event rows.
SELECT p.id AS player_id, COUNT(s.id) AS sessions,
 SUM(s.status = 'completed') AS completed,
 AVG(CASE WHEN s.status = 'completed' THEN s.duration_ms END) / 1000 AS avg_completed_seconds
FROM telemetry_player p
JOIN telemetry_playsession s ON s.player_id = p.id
WHERE p.source = @source AND s.started_at >= @window_start AND s.started_at < @window_end
GROUP BY p.id;

-- Timeline for one player. UUID is stored as CHAR(32), without hyphens.
-- SELECT e.* FROM telemetry_behaviorevent e
-- JOIN telemetry_playsession s ON s.id=e.session_id
-- WHERE s.player_id='YOUR_32_CHARACTER_UUID'
-- ORDER BY e.occurred_at, e.sequence;


-- Structured problem metrics. Started-run cohort, followed through current outcome.
-- Do not join all attempts/events into this aggregation: it would duplicate runs.
SELECT t.task_id,t.content_version,t.title,COUNT(r.id) AS started_runs,
 SUM(r.status='completed') AS completed_runs,
 ROUND(100.0*SUM(r.status='completed')/NULLIF(COUNT(r.id),0),1) AS completion_rate,
 SUM(r.status='abandoned') AS abandoned_runs,
 AVG(CASE WHEN r.status='completed' THEN r.active_ms END)/1000 AS avg_active_seconds
FROM telemetry_taskrun r
JOIN telemetry_learningtask t ON r.task_id=t.id
JOIN telemetry_playsession s ON r.session_id=s.id
JOIN telemetry_player p ON s.player_id=p.id
WHERE p.source=@source AND r.started_at>=@window_start AND r.started_at<@window_end
GROUP BY t.task_id,t.content_version,t.title;

-- Operation failures by reason. Event-window metric (not run-cohort metric).
SELECT e.operation,e.failure_reason,COUNT(*) AS failures
FROM telemetry_behaviorevent e
JOIN telemetry_playsession s ON e.session_id=s.id
JOIN telemetry_player p ON s.player_id=p.id
WHERE p.source=@source AND e.event_type='operation_failed'
 AND e.occurred_at>=@window_start AND e.occurred_at<@window_end
GROUP BY e.operation,e.failure_reason ORDER BY failures DESC;
