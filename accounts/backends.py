from django.contrib.auth.backends import ModelBackend


class AdminBackend(ModelBackend):
    """Also deny legacy learner sessions on every request, not only at login."""
    def user_can_authenticate(self, user):
        return super().user_can_authenticate(user) and user.role == 'admin'
