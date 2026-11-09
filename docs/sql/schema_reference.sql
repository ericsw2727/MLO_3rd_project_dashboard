-- NODEVERSE current MySQL schema; schema only, no row data.
-- Apply migrations with manage.py migrate. Do not rerun this DDL on the existing database.
-- v2: task versions, task encounters, solution attempts and structured behavior.

-- accounts_user
CREATE TABLE `accounts_user` (
  `password` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  `last_login` datetime(6) DEFAULT NULL,
  `is_superuser` tinyint(1) NOT NULL,
  `username` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `first_name` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `last_name` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `email` varchar(254) COLLATE utf8mb4_unicode_ci NOT NULL,
  `is_staff` tinyint(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `date_joined` datetime(6) NOT NULL,
  `id` char(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `display_name` varchar(80) COLLATE utf8mb4_unicode_ci NOT NULL,
  `role` varchar(7) COLLATE utf8mb4_unicode_ci NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`),
  CONSTRAINT `valid_user_role` CHECK ((`role` in (_utf8mb4'learner',_utf8mb4'admin')))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- accounts_user_groups
CREATE TABLE `accounts_user_groups` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` char(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `group_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `accounts_user_groups_user_id_group_id_59c0b32f_uniq` (`user_id`,`group_id`),
  KEY `accounts_user_groups_group_id_bd11a704_fk_auth_group_id` (`group_id`),
  CONSTRAINT `accounts_user_groups_group_id_bd11a704_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`),
  CONSTRAINT `accounts_user_groups_user_id_52b62117_fk_accounts_user_id` FOREIGN KEY (`user_id`) REFERENCES `accounts_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- accounts_user_user_permissions
CREATE TABLE `accounts_user_user_permissions` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` char(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `permission_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `accounts_user_user_permi_user_id_permission_id_2ab516c2_uniq` (`user_id`,`permission_id`),
  KEY `accounts_user_user_p_permission_id_113bb443_fk_auth_perm` (`permission_id`),
  CONSTRAINT `accounts_user_user_p_permission_id_113bb443_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `accounts_user_user_p_user_id_e4f0a161_fk_accounts_` FOREIGN KEY (`user_id`) REFERENCES `accounts_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- auth_group
CREATE TABLE `auth_group` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- auth_group_permissions
CREATE TABLE `auth_group_permissions` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `group_id` int NOT NULL,
  `permission_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_group_permissions_group_id_permission_id_0cd325b0_uniq` (`group_id`,`permission_id`),
  KEY `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` (`permission_id`),
  CONSTRAINT `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_group_permissions_group_id_b120cbf9_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- auth_permission
CREATE TABLE `auth_permission` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `content_type_id` int NOT NULL,
  `codename` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_permission_content_type_id_codename_01ab375a_uniq` (`content_type_id`,`codename`),
  CONSTRAINT `auth_permission_content_type_id_2f476e4b_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- django_content_type
CREATE TABLE `django_content_type` (
  `id` int NOT NULL AUTO_INCREMENT,
  `app_label` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `model` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `django_content_type_app_label_model_76bd3d3b_uniq` (`app_label`,`model`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- django_migrations
CREATE TABLE `django_migrations` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `app` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `applied` datetime(6) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- django_session
CREATE TABLE `django_session` (
  `session_key` varchar(40) COLLATE utf8mb4_unicode_ci NOT NULL,
  `session_data` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `expire_date` datetime(6) NOT NULL,
  PRIMARY KEY (`session_key`),
  KEY `django_session_expire_date_a5c62663` (`expire_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- telemetry_behaviorevent
CREATE TABLE `telemetry_behaviorevent` (
  `id` char(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `sequence` int unsigned NOT NULL,
  `event_type` varchar(24) COLLATE utf8mb4_unicode_ci NOT NULL,
  `occurred_at` datetime(6) NOT NULL,
  `received_at` datetime(6) NOT NULL,
  `payload` json NOT NULL,
  `session_id` char(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `failure_reason` varchar(80) COLLATE utf8mb4_unicode_ci NOT NULL,
  `hint_id` varchar(80) COLLATE utf8mb4_unicode_ci NOT NULL,
  `hint_step` smallint unsigned DEFAULT NULL,
  `operation` varchar(40) COLLATE utf8mb4_unicode_ci NOT NULL,
  `state_after` json NOT NULL DEFAULT (_utf8mb4'{}'),
  `state_before` json NOT NULL DEFAULT (_utf8mb4'{}'),
  `attempt_id` char(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `run_id` char(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `event_session_sequence_unique` (`session_id`,`sequence`),
  KEY `event_session_time` (`session_id`,`occurred_at`),
  KEY `event_time_type` (`occurred_at`,`event_type`),
  KEY `telemetry_behaviorev_attempt_id_a90ee0fe_fk_telemetry` (`attempt_id`),
  KEY `telemetry_behaviorevent_run_id_cf20b7cb_fk_telemetry_taskrun_id` (`run_id`),
  CONSTRAINT `telemetry_behaviorev_attempt_id_a90ee0fe_fk_telemetry` FOREIGN KEY (`attempt_id`) REFERENCES `telemetry_solveattempt` (`id`),
  CONSTRAINT `telemetry_behaviorev_session_id_f02cd60e_fk_telemetry` FOREIGN KEY (`session_id`) REFERENCES `telemetry_playsession` (`id`),
  CONSTRAINT `telemetry_behaviorevent_run_id_cf20b7cb_fk_telemetry_taskrun_id` FOREIGN KEY (`run_id`) REFERENCES `telemetry_taskrun` (`id`),
  CONSTRAINT `event_sequence_positive` CHECK ((`sequence` >= 1)),
  CONSTRAINT `event_type_valid` CHECK ((`event_type` in (_utf8mb4'attempt',_utf8mb4'success',_utf8mb4'failure',_utf8mb4'hint',_utf8mb4'level_start',_utf8mb4'task_started',_utf8mb4'task_completed',_utf8mb4'task_abandoned',_utf8mb4'attempt_started',_utf8mb4'attempt_failed',_utf8mb4'attempt_succeeded',_utf8mb4'operation_succeeded',_utf8mb4'operation_failed',_utf8mb4'paused',_utf8mb4'resumed'))),
  CONSTRAINT `telemetry_behaviorevent_chk_1` CHECK ((`sequence` >= 0)),
  CONSTRAINT `telemetry_behaviorevent_chk_2` CHECK ((`hint_step` >= 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- telemetry_learningtask
CREATE TABLE `telemetry_learningtask` (
  `id` char(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `task_id` varchar(80) COLLATE utf8mb4_unicode_ci NOT NULL,
  `content_version` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL,
  `title` varchar(120) COLLATE utf8mb4_unicode_ci NOT NULL,
  `topic` varchar(10) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `task_version_unique` (`task_id`,`content_version`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- telemetry_player
CREATE TABLE `telemetry_player` (
  `id` char(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `external_id` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `display_name` varchar(80) COLLATE utf8mb4_unicode_ci NOT NULL,
  `source` varchar(8) COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `external_id` (`external_id`),
  CONSTRAINT `player_source_valid` CHECK ((`source` in (_utf8mb4'live',_utf8mb4'demo')))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- telemetry_playsession
CREATE TABLE `telemetry_playsession` (
  `id` char(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `topic` varchar(10) COLLATE utf8mb4_unicode_ci NOT NULL,
  `level` smallint unsigned NOT NULL,
  `game_version` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL,
  `started_at` datetime(6) NOT NULL,
  `ended_at` datetime(6) DEFAULT NULL,
  `status` varchar(12) COLLATE utf8mb4_unicode_ci NOT NULL,
  `duration_ms` int unsigned DEFAULT NULL,
  `player_id` char(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  KEY `session_player_time` (`player_id`,`started_at`),
  KEY `session_time_topic` (`started_at`,`topic`),
  CONSTRAINT `telemetry_playsession_player_id_0bf4a70e_fk_telemetry_player_id` FOREIGN KEY (`player_id`) REFERENCES `telemetry_player` (`id`),
  CONSTRAINT `session_status_valid` CHECK ((`status` in (_utf8mb4'completed',_utf8mb4'abandoned',_utf8mb4'in_progress'))),
  CONSTRAINT `session_time_valid` CHECK (((`ended_at` is null) or (`ended_at` >= `started_at`))),
  CONSTRAINT `session_topic_valid` CHECK ((`topic` in (_utf8mb4'stack',_utf8mb4'queue',_utf8mb4'tree'))),
  CONSTRAINT `telemetry_playsession_chk_1` CHECK ((`level` >= 0)),
  CONSTRAINT `telemetry_playsession_chk_2` CHECK ((`duration_ms` >= 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- telemetry_solveattempt
CREATE TABLE `telemetry_solveattempt` (
  `id` char(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `number` int unsigned NOT NULL,
  `started_at` datetime(6) NOT NULL,
  `ended_at` datetime(6) DEFAULT NULL,
  `outcome` varchar(12) COLLATE utf8mb4_unicode_ci NOT NULL,
  `run_id` char(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `attempt_number_unique` (`run_id`,`number`),
  CONSTRAINT `telemetry_solveattempt_run_id_600a8218_fk_telemetry_taskrun_id` FOREIGN KEY (`run_id`) REFERENCES `telemetry_taskrun` (`id`),
  CONSTRAINT `attempt_number_positive` CHECK ((`number` >= 1)),
  CONSTRAINT `attempt_outcome_valid` CHECK ((`outcome` in (_utf8mb4'success',_utf8mb4'failure',_utf8mb4'abandoned',_utf8mb4'in_progress'))),
  CONSTRAINT `attempt_time_valid` CHECK (((`ended_at` is null) or (`ended_at` >= `started_at`))),
  CONSTRAINT `telemetry_solveattempt_chk_1` CHECK ((`number` >= 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- telemetry_taskrun
CREATE TABLE `telemetry_taskrun` (
  `id` char(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `started_at` datetime(6) NOT NULL,
  `ended_at` datetime(6) DEFAULT NULL,
  `status` varchar(12) COLLATE utf8mb4_unicode_ci NOT NULL,
  `active_ms` int unsigned DEFAULT NULL,
  `paused_ms` int unsigned NOT NULL,
  `session_id` char(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `task_id` char(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  KEY `telemetry_taskrun_session_id_4f561bec_fk_telemetry` (`session_id`),
  KEY `task_run_time` (`task_id`,`started_at`),
  CONSTRAINT `telemetry_taskrun_session_id_4f561bec_fk_telemetry` FOREIGN KEY (`session_id`) REFERENCES `telemetry_playsession` (`id`),
  CONSTRAINT `telemetry_taskrun_task_id_24795a5c_fk_telemetry_learningtask_id` FOREIGN KEY (`task_id`) REFERENCES `telemetry_learningtask` (`id`),
  CONSTRAINT `run_status_valid` CHECK ((`status` in (_utf8mb4'completed',_utf8mb4'abandoned',_utf8mb4'in_progress'))),
  CONSTRAINT `run_time_valid` CHECK (((`ended_at` is null) or (`ended_at` >= `started_at`))),
  CONSTRAINT `telemetry_taskrun_chk_1` CHECK ((`active_ms` >= 0)),
  CONSTRAINT `telemetry_taskrun_chk_2` CHECK ((`paused_ms` >= 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
