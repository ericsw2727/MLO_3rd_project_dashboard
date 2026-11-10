import uuid
from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models


def auth_field_with_column(field_name, column_name):
    """Keep Django authentication behavior while exposing a readable SQL column."""
    field = AbstractUser._meta.get_field(field_name).clone()
    field.db_column = column_name
    return field

class AccountManager(UserManager):
    def create_user(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('role', 'admin')
        return super().create_user(username, email, password, **extra_fields)

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields['role'] = 'admin'
        return super().create_superuser(username, email, password, **extra_fields)

class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False,
                          db_column='admin_id', db_comment='관리자 고유 UUID')
    username = auth_field_with_column('username', 'login_id')
    password = auth_field_with_column('password', 'password_hash')
    last_login = auth_field_with_column('last_login', 'last_login_at')
    date_joined = auth_field_with_column('date_joined', 'created_at')
    groups = models.ManyToManyField('auth.Group', blank=True, related_name='user_set', related_query_name='user',
                                    db_table='admin_group_memberships', verbose_name='groups',
                                    help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.')
    user_permissions = models.ManyToManyField('auth.Permission', blank=True, related_name='user_set', related_query_name='user',
                                              db_table='admin_permission_assignments', verbose_name='user permissions',
                                              help_text='Specific permissions for this user.')
    display_name = models.CharField(max_length=80, db_column='nickname', db_comment='화면에 표시할 관리자 이름')
    role = models.CharField(max_length=7, choices=[('learner', 'Legacy account'), ('admin', 'Admin')], default='admin',
                            db_column='account_role', db_comment='admin: 관리자, learner: 로그인 불가한 과거 계정')
    updated_at = models.DateTimeField(auto_now=True, db_comment='관리자 정보 최종 수정 시각')
    objects = AccountManager()
    REQUIRED_FIELDS = ['display_name']

    class Meta:
        db_table = 'admin_accounts'
        db_table_comment = '대시보드 관리자 계정. 게임 회원은 game_members에서 관리'
        constraints = [models.CheckConstraint(condition=models.Q(role__in=['learner', 'admin']), name='valid_user_role')]
