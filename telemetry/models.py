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
