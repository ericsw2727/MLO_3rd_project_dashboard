from django.contrib.auth.backends import ModelBackend
from django.conf import settings
from .development import TEST_ADMIN_ID


class AdminBackend(ModelBackend):
    """Also deny legacy learner sessions on every request, not only at login."""
    def user_can_authenticate(self, user):
        return (super().user_can_authenticate(user) and user.role == 'admin'
                and (user.pk != TEST_ADMIN_ID or settings.DEBUG))
