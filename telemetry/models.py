import uuid
from django.db import models
from django.db.models import Q, F


class Player(models.Model):
    """Analysis subject, with no password, role, or web-login capabilities."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False,
                          db_column='member_id', db_comment='대시보드 회원 UUID. MongoDB의 player_id와 연결')
    external_id = models.CharField(max_length=150, unique=True, db_column='external_member_key',
                                   db_comment='외부 회원 연결 키. 예: game:member:게임서버회원ID')
    display_name = models.CharField(max_length=80, db_column='nickname', db_comment='게임 회원 표시 이름')
    source = models.CharField(max_length=8, choices=[('live', '실제'), ('demo', '데모')], default='live',
                              db_column='data_source', db_comment='live: 실제 회원, demo: 데모 데이터')
    created_at = models.DateTimeField(auto_now_add=True, db_column='registered_at', db_comment='대시보드에 최초 등록된 시각')

    class Meta:
        db_table = 'game_members'
        db_table_comment = '게임 회원 식별 정보. 비밀번호와 플레이 로그는 저장하지 않음'
        constraints = [models.CheckConstraint(condition=Q(source__in=['live', 'demo']), name='player_source_valid')]


class GameAccount(models.Model):
    """Game client player account with PBKDF2 password hash, recovery key, and cloud save JSON."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    player = models.OneToOneField(Player, on_delete=models.CASCADE, related_name='game_account')
    username = models.CharField(max_length=60, unique=True, db_comment='게임 로그인 아이디')
    password_hash = models.CharField(max_length=255, db_comment='PBKDF2 암호화 비밀번호 해시')
    recovery_key = models.CharField(max_length=120, blank=True, default='', db_index=True, db_comment='아이디/비밀번호 찾기용 복구 키')
    save_data = models.JSONField(default=dict, blank=True, db_comment='클라우드 세이브 (난이도, 점수, 3D 위치, 2D 별점)')
    created_at = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'game_accounts'
        db_table_comment = '게임 클라이언트 회원 계정 및 클라우드 세이브 데이터'


class PlaySession(models.Model):
    TOPICS = [('stack', '스택'), ('queue', '큐'), ('tree', '트리')]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    player = models.ForeignKey(Player, on_delete=models.PROTECT, related_name='play_sessions')
    topic = models.CharField(max_length=10, choices=TOPICS)
    level = models.PositiveSmallIntegerField(default=1)
    game_version = models.CharField(max_length=30, default='demo-1.0')
    started_at = models.DateTimeField()
    ended_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=12, choices=[('completed', '완료'), ('abandoned', '중단'), ('in_progress', '진행 중')])
    duration_ms = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        db_table = 'game_sessions'
        managed = False  # Stored by telemetry.mongo, never in MySQL.
        indexes = [models.Index(fields=['player', 'started_at'], name='session_player_time'),
                   models.Index(fields=['started_at', 'topic'], name='session_time_topic')]
        constraints = [models.CheckConstraint(condition=Q(topic__in=['stack', 'queue', 'tree']), name='session_topic_valid'),
                       models.CheckConstraint(condition=Q(status__in=['completed', 'abandoned', 'in_progress']), name='session_status_valid'),
                       models.CheckConstraint(condition=Q(ended_at__isnull=True) | Q(ended_at__gte=F('started_at')), name='session_time_valid')]


class LearningTask(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task_id = models.CharField(max_length=80)
    content_version = models.CharField(max_length=30)
    title = models.CharField(max_length=120)
    topic = models.CharField(max_length=10, choices=PlaySession.TOPICS)
    class Meta:
        db_table = 'game_problems'
        managed = False
        constraints = [models.UniqueConstraint(fields=['task_id', 'content_version'], name='task_version_unique')]


class TaskRun(models.Model):
    """One encounter with a problem. Repeated solution attempts belong to this run."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(PlaySession, on_delete=models.PROTECT, related_name='task_runs')
    task = models.ForeignKey(LearningTask, on_delete=models.PROTECT, related_name='runs')
    started_at = models.DateTimeField()
    ended_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=12, choices=[('completed', '해결'), ('abandoned', '포기'), ('in_progress', '진행 중')])
    active_ms = models.PositiveIntegerField(null=True, blank=True)
    paused_ms = models.PositiveIntegerField(default=0)
    def clean(self):
        from django.core.exceptions import ValidationError
        if self.task_id and self.session_id and self.task.topic != self.session.topic:
            raise ValidationError('문제 자료구조와 세션 자료구조가 다릅니다.')
        if self.ended_at and self.started_at:
            elapsed = int((self.ended_at-self.started_at).total_seconds()*1000)
            if self.paused_ms > elapsed or (self.active_ms is not None and self.active_ms + self.paused_ms != elapsed):
                raise ValidationError('실제 풀이 시간과 일시정지 시간이 전체 경과 시간과 맞지 않습니다.')
    class Meta:
        db_table = 'problem_runs'
        managed = False
        indexes = [models.Index(fields=['task', 'started_at'], name='task_run_time')]
        constraints = [models.CheckConstraint(condition=Q(status__in=['completed', 'abandoned', 'in_progress']), name='run_status_valid'),
                       models.CheckConstraint(condition=Q(ended_at__isnull=True) | Q(ended_at__gte=F('started_at')), name='run_time_valid')]


class SolveAttempt(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    run = models.ForeignKey(TaskRun, on_delete=models.PROTECT, related_name='attempts')
    number = models.PositiveIntegerField()
    started_at = models.DateTimeField()
    ended_at = models.DateTimeField(null=True, blank=True)
    outcome = models.CharField(max_length=12, choices=[('success', '성공'), ('failure', '실패'), ('abandoned', '포기'), ('in_progress', '진행 중')])
    class Meta:
        db_table = 'solution_attempts'
        managed = False
        constraints = [models.UniqueConstraint(fields=['run', 'number'], name='attempt_number_unique'),
                       models.CheckConstraint(condition=Q(number__gte=1), name='attempt_number_positive'),
                       models.CheckConstraint(condition=Q(outcome__in=['success', 'failure', 'abandoned', 'in_progress']), name='attempt_outcome_valid'),
                       models.CheckConstraint(condition=Q(ended_at__isnull=True) | Q(ended_at__gte=F('started_at')), name='attempt_time_valid')]


class BehaviorEvent(models.Model):
    TYPES = [('attempt', '이전 시도'), ('success', '이전 성공'), ('failure', '이전 실패'), ('hint', '힌트'), ('level_start', '이전 레벨 시작'),
             ('task_started', '문제 시작'), ('task_completed', '문제 해결'), ('task_abandoned', '문제 포기'),
             ('attempt_started', '풀이 시도'), ('attempt_failed', '시도 실패'), ('attempt_succeeded', '시도 성공'),
             ('operation_succeeded', '연산 성공'), ('operation_failed', '연산 실패'), ('paused', '일시정지'), ('resumed', '재개')]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(PlaySession, on_delete=models.PROTECT, related_name='events')
    sequence = models.PositiveIntegerField()
    event_type = models.CharField(max_length=24, choices=TYPES)
    run = models.ForeignKey(TaskRun, null=True, blank=True, on_delete=models.PROTECT, related_name='events')
    attempt = models.ForeignKey(SolveAttempt, null=True, blank=True, on_delete=models.PROTECT, related_name='events')
    operation = models.CharField(max_length=40, blank=True)
    failure_reason = models.CharField(max_length=80, blank=True)
    state_before = models.JSONField(default=dict, blank=True)
    state_after = models.JSONField(default=dict, blank=True)
    hint_id = models.CharField(max_length=80, blank=True)
    hint_step = models.PositiveSmallIntegerField(null=True, blank=True)
    occurred_at = models.DateTimeField()
    received_at = models.DateTimeField(auto_now_add=True)
    payload = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'gameplay_events'
        managed = False
        ordering = ['occurred_at', 'sequence', 'id']
        indexes = [models.Index(fields=['session', 'occurred_at'], name='event_session_time'),
                   models.Index(fields=['occurred_at', 'event_type'], name='event_time_type')]
        constraints = [models.UniqueConstraint(fields=['session', 'sequence'], name='event_session_sequence_unique'),
                       models.CheckConstraint(condition=Q(sequence__gte=1), name='event_sequence_positive'),
                       models.CheckConstraint(condition=Q(event_type__in=['attempt', 'success', 'failure', 'hint', 'level_start', 'task_started', 'task_completed', 'task_abandoned', 'attempt_started', 'attempt_failed', 'attempt_succeeded', 'operation_succeeded', 'operation_failed', 'paused', 'resumed']), name='event_type_valid')]

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.run_id and self.run.session_id != self.session_id:
            raise ValidationError('문제와 이벤트의 세션이 일치하지 않습니다.')
        if self.attempt_id and (not self.run_id or self.attempt.run_id != self.run_id):
            raise ValidationError('시도와 이벤트의 문제 실행이 일치하지 않습니다.')
        if self.attempt_id and self.occurred_at and (self.occurred_at < self.attempt.started_at or
                (self.attempt.ended_at and self.occurred_at > self.attempt.ended_at)):
            raise ValidationError('이벤트 시각이 풀이 시도 범위 밖입니다.')
        if self.event_type == 'operation_failed' and (not self.operation or not self.failure_reason):
            raise ValidationError('연산 실패에는 연산과 실패 원인이 필요합니다.')
        if self.event_type == 'operation_succeeded' and not self.operation:
            raise ValidationError('연산 성공에는 연산 이름이 필요합니다.')
        if self.event_type not in ('attempt', 'success', 'failure', 'hint', 'level_start') and not self.run_id:
            raise ValidationError('새 형식 이벤트에는 문제 실행이 필요합니다.')
        if self.event_type.startswith(('attempt_', 'operation_')) and not self.attempt_id:
            raise ValidationError('시도·연산 이벤트에는 풀이 시도가 필요합니다.')
        if self.event_type == 'hint' and self.run_id and (not self.hint_id or not self.hint_step):
            raise ValidationError('구조화된 힌트에는 종류와 1 이상의 단계가 필요합니다.')
        if not all(isinstance(value, dict) for value in (self.state_before, self.state_after, self.payload)):
            raise ValidationError('상태와 추가 데이터는 JSON 객체여야 합니다.')



class GameLoginRecord(models.Model):
    """Every sign-up, login, and account recovery attempt from the game, success or failure."""
    KINDS = [('register', '회원가입'), ('login', '로그인'), ('find_id', '아이디 찾기'), ('reset', '비밀번호 재설정')]
    id = models.BigAutoField(primary_key=True)
    player = models.ForeignKey(Player, on_delete=models.SET_NULL, null=True, blank=True, related_name='login_records',
                               db_column='member_id')
    login_id = models.CharField(max_length=60, db_comment='요청에 사용된 게임 아이디 (game_accounts.username)')
    kind = models.CharField(max_length=8, choices=KINDS)
    success = models.BooleanField()
    failure_reason = models.CharField(max_length=30, blank=True, default='')
    install_id = models.CharField(max_length=64, blank=True, default='',
                                  db_comment='게임 설치 ID. MongoDB 학습 로그의 player_id와 연결')
    build_version = models.CharField(max_length=20, blank=True, default='')
    content_version = models.CharField(max_length=40, blank=True, default='')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    occurred_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'game_login_history'
        db_table_comment = '게임 회원가입·로그인 기록'
        indexes = [models.Index(fields=['occurred_at']), models.Index(fields=['install_id'])]


class GameRelease(models.Model):
    """One EXE release per channel; the newest active one is served in the manifest."""
    channel = models.CharField(max_length=30, default='windows-stable')
    build_version = models.CharField(max_length=20, db_comment='주.부.수 형식 EXE 버전')
    min_build = models.CharField(max_length=20, db_comment='이보다 낮은 EXE는 필수 업데이트')
    download_page = models.URLField(blank=True, default='', db_comment='비우면 이 서버의 /download/')
    package = models.FileField(upload_to='builds/', blank=True, default='', db_comment='EXE ZIP 파일 (선택)')
    package_url = models.URLField(blank=True, default='', db_comment='외부 EXE ZIP 주소 (선택)')
    notes = models.CharField(max_length=500, blank=True, default='')
    is_active = models.BooleanField(default=True)
    published_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'game_releases'
        db_table_comment = '게임 EXE 릴리스와 업데이트 기준'
        constraints = [models.UniqueConstraint(fields=['channel', 'build_version'], name='release_channel_build_unique')]


class ContentPack(models.Model):
    """Resource pack (.pck). SHA-256 and size are always computed by the server."""
    version = models.CharField(max_length=40, unique=True, db_comment='예: content-2026.11.19')
    file = models.FileField(upload_to='packs/')
    sha256 = models.CharField(max_length=64)
    size = models.PositiveBigIntegerField()
    min_build = models.CharField(max_length=20)
    is_active = models.BooleanField(default=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'game_content_packs'
        db_table_comment = '게임 리소스 팩. 해시·크기는 서버 계산값'
