-- Run ONCE in MySQL Workbench using a server administrator account.
-- The first result contains a generated password: save it privately.
-- This script deliberately grants no access to administrator/Django tables.
CREATE USER 'nodeverse_ingest'@'192.168.0.81'
    IDENTIFIED BY RANDOM PASSWORD;

GRANT SELECT, INSERT, UPDATE ON nodeverse.game_members
    TO 'nodeverse_ingest'@'192.168.0.81';

SHOW GRANTS FOR 'nodeverse_ingest'@'192.168.0.81';
