-- MySQL stores members and administrators; learning records are in MongoDB.
SELECT member_id, external_member_key, nickname, data_source, registered_at
FROM game_members ORDER BY registered_at DESC;

SELECT data_source, COUNT(*) AS member_count FROM game_members GROUP BY data_source;

-- Deliberately excludes password hashes.
SELECT admin_id, login_id, nickname, account_role, is_active
FROM admin_accounts ORDER BY created_at DESC;
