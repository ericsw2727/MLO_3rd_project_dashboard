"""Local-only development login. This account cannot authenticate in production."""
from urllib.parse import urlsplit
from uuid import UUID
from django.conf import settings

TEST_ADMIN_ID = UUID('7aa1817e-10dd-4bcf-8bab-083f114764a9')
TEST_ADMIN_USERNAME = '__local_test_admin__'


def local_test_login_allowed(request):
    return (
        settings.DEBUG
        and request.META.get('REMOTE_ADDR') in ('127.0.0.1', '::1')
        and urlsplit('//' + request.get_host()).hostname in ('localhost', '127.0.0.1', '::1')
        and not any(name in request.META for name in ('HTTP_FORWARDED', 'HTTP_X_FORWARDED_FOR', 'HTTP_X_FORWARDED_HOST'))
    )
