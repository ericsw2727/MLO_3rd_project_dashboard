import uuid
from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models

class AccountManager(UserManager):
    def create_user(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('role', 'admin')
        return super().create_user(username, email, password, **extra_fields)

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields['role'] = 'admin'
        return super().create_superuser(username, email, password, **extra_fields)

class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    display_name = models.CharField(max_length=80)
    role = models.CharField(max_length=7, choices=[('learner', 'Legacy account'), ('admin', 'Admin')], default='admin')
    updated_at = models.DateTimeField(auto_now=True)
    objects = AccountManager()
    REQUIRED_FIELDS = ['display_name']

    class Meta:
        constraints = [models.CheckConstraint(condition=models.Q(role__in=['learner', 'admin']), name='valid_user_role')]
