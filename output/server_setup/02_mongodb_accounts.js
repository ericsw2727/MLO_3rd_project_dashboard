// Run ONCE in mongosh ON THE SERVER PC, connected to localhost:27017.
// Passwords are entered locally with passwordPrompt(), never stored in this file.
// Create these accounts BEFORE enabling authorization in mongod.cfg.
// If an account already exists, stop and inspect it; do not overwrite its roles/password.
const securityDb = db.getSiblingDB('admin');
const logsDb = db.getSiblingDB('nodeverse_logs');
for (const [database, username] of [
    [securityDb, 'nodeverse_security_admin'],
    [logsDb, 'nodeverse_ingest'],
    [logsDb, 'nodeverse_dashboard_reader'],
]) {
    if (database.getUser(username)) throw new Error('Account already exists; inspect first: ' + username);
}
if (logsDb.getRole('nodeverse_ingest_records')) throw new Error('Role exists; inspect it before proceeding.');

print('1/3: Set a separate SERVER ADMINISTRATOR password.');
securityDb.createUser({
    user: 'nodeverse_security_admin', pwd: passwordPrompt(),
    roles: [{role: 'userAdminAnyDatabase', db: 'admin'}],
});

logsDb.createRole({
    role: 'nodeverse_ingest_records',
    privileges: [
        {resource: {db: 'nodeverse_logs', collection: ''}, actions: ['listCollections']},
        ...['game_sessions', 'game_problems', 'problem_runs', 'solution_attempts', 'gameplay_events'].map(collection => ({
            resource: {db: 'nodeverse_logs', collection},
            actions: ['find', 'insert', 'update', 'listIndexes'],
        })),
    ],
    roles: [],
});
print('2/3: Set a separate SENDER password for 192.168.0.81.');
logsDb.createUser({
    user: 'nodeverse_ingest', pwd: passwordPrompt(),
    roles: [{role: 'nodeverse_ingest_records', db: 'nodeverse_logs'}],
    authenticationRestrictions: [{clientSource: ['192.168.0.81']}],
});
print('3/3: Set a separate DASHBOARD read-only password.');
logsDb.createUser({
    user: 'nodeverse_dashboard_reader', pwd: passwordPrompt(),
    roles: [{role: 'read', db: 'nodeverse_logs'}],
    authenticationRestrictions: [{clientSource: ['192.168.0.29', '192.168.0.167', '127.0.0.1', '::1']}],
});
print('Accounts created. Authorization is NOT enabled by this script. Follow the local instructions before handoff.');
