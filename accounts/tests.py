import json
from django.contrib.auth import get_user_model
from django.test import Client, SimpleTestCase, TestCase, override_settings

User = get_user_model()


class PublicContractTests(SimpleTestCase):
    def test_csrf_and_public_pages(self):
        client = Client(enforce_csrf_checks=True)
        for path in ['/staff/login/', '/staff/register/']:
            self.assertContains(client.get(path), 'csrfmiddlewaretoken')
        self.assertEqual(client.post('/api/auth/login', '{}', content_type='application/json').status_code, 403)
        self.assertIn('csrf_token', client.get('/api/auth/csrf').json())

    def test_anonymous_protected_routes(self):
        # The integrated public homepage is accessible; analytics remain protected.
        self.assertEqual(self.client.get('/').status_code, 200)
        for path in ['/staff/', '/staff/players/', '/staff/events/']:
            self.assertRedirects(self.client.get(path), '/staff/login/')
        for path in ['/api/auth/me', '/api/admin/summary', '/api/admin/players', '/api/admin/events']:
            self.assertEqual(self.client.get(path).status_code, 401)

    def test_old_public_pages_are_admin_aliases(self):
        self.assertRedirects(self.client.get('/register/'), '/staff/register/')
        self.assertRedirects(self.client.get('/login/'), '/staff/login/')
        self.assertEqual(self.client.post('/register/', {}).status_code, 405)


@override_settings(DEBUG=True)
class LocalTestAdminTests(TestCase):
    def test_button_csrf_login_and_account_reuse(self):
        from .development import TEST_ADMIN_ID
        client = Client(enforce_csrf_checks=True)
        self.assertContains(client.get('/staff/login/', HTTP_HOST='localhost'), '/staff/test-login/')
        self.assertFalse(User.objects.exists())
        self.assertEqual(client.post('/staff/test-login/', HTTP_HOST='localhost').status_code, 403)
        token = client.cookies['csrftoken'].value
        response = client.post('/staff/test-login/', HTTP_HOST='localhost', HTTP_X_CSRFTOKEN=token)
        self.assertRedirects(response, '/staff/', fetch_redirect_response=False)
        account = User.objects.get(pk=TEST_ADMIN_ID)
        self.assertFalse(account.has_usable_password())
        self.assertFalse(account.is_superuser)
        self.assertEqual(client.get('/api/auth/me').json()['user']['user_id'], str(TEST_ADMIN_ID))
        self.assertEqual(client.session.get_expiry_age(), 3600)
        token = client.cookies['csrftoken'].value
        self.assertEqual(client.post('/staff/test-login/', HTTP_HOST='localhost', HTTP_X_CSRFTOKEN=token).status_code, 302)
        self.assertEqual(User.objects.count(), 1)
        with override_settings(DEBUG=False):
            self.assertEqual(client.get('/api/auth/me').status_code, 401)

    def test_external_production_and_proxy_requests_are_denied(self):
        for extra in [
            {'REMOTE_ADDR': '192.168.0.50', 'HTTP_HOST': 'localhost'},
            {'HTTP_HOST': 'testserver'},
            {'HTTP_HOST': 'localhost', 'HTTP_X_FORWARDED_FOR': '192.168.0.50'},
        ]:
            self.assertNotContains(self.client.get('/staff/login/', **extra), '/staff/test-login/')
            self.assertEqual(self.client.post('/staff/test-login/', **extra).status_code, 403)
        with override_settings(DEBUG=False):
            self.assertNotContains(self.client.get('/staff/login/', HTTP_HOST='localhost'), '/staff/test-login/')
            self.assertEqual(self.client.post('/staff/test-login/', HTTP_HOST='localhost').status_code, 403)
        self.assertFalse(User.objects.exists())
        self.assertEqual(self.client.get('/staff/test-login/', HTTP_HOST='localhost').status_code, 405)

    def test_disabled_account_is_not_reactivated(self):
        from .development import TEST_ADMIN_ID, TEST_ADMIN_USERNAME
        account = User(id=TEST_ADMIN_ID, username=TEST_ADMIN_USERNAME, role='admin', is_active=False)
        account.set_unusable_password()
        account.save()
        self.assertEqual(self.client.post('/staff/test-login/', HTTP_HOST='localhost').status_code, 403)
        account.refresh_from_db()
        self.assertFalse(account.is_active)


@override_settings(ADMIN_REGISTRATION_CODE='test-invite-only')
class AdminAuthTests(TestCase):
    password = 'Admin-Only!4972'

    def test_readable_sql_names_preserve_auth_and_permission_relations(self):
        from django.contrib.auth.models import Group, Permission
        from django.db import connection
        user = User.objects.create_user('schema-admin', password=self.password, display_name='Schema admin')
        group = Group.objects.create(name='Schema operators')
        permission = Permission.objects.filter(codename='view_user', content_type__app_label='accounts').get()
        user.groups.add(group)
        group.permissions.add(permission)
        user.user_permissions.add(permission)
        self.assertTrue(user.has_perm('accounts.view_user'))
        self.assertTrue(user.check_password(self.password))
        with connection.cursor() as cursor:
            columns = {column.name for column in connection.introspection.get_table_description(cursor, 'admin_accounts')}
        self.assertTrue({'admin_id', 'login_id', 'password_hash', 'nickname', 'account_role', 'created_at', 'last_login_at'} <= columns)
        self.assertEqual(user.groups.get().pk, group.pk)
        self.assertEqual(user.user_permissions.get().pk, permission.pk)
        self.assertIn('admin_group_memberships', connection.introspection.table_names())
        self.assertIn('admin_permission_assignments', connection.introspection.table_names())

    def register(self, name='operator', **extra):
        return self.client.post('/api/auth/register', json.dumps({
            'login_id': name, 'display_name': '운영자', 'password': self.password,
            'password_confirm': self.password, 'invitation_code': 'test-invite-only', **extra}), content_type='application/json')

    def signin(self, name='operator', password=None, client=None):
        return (client or self.client).post('/api/auth/login', json.dumps({
            'login_id': name, 'password': password or self.password}), content_type='application/json')

    def test_registration_invitation_duplicate_and_hash(self):
        self.assertEqual(self.register(invitation_code='wrong').status_code, 400)
        self.assertFalse(User.objects.exists())
        response = self.register(role='learner')
        self.assertEqual(response.status_code, 201)
        user = User.objects.get(username='operator')
        self.assertEqual(user.role, 'admin')
        self.assertTrue(user.check_password(self.password))
        self.assertNotEqual(user.password, self.password)
        self.assertNotIn('password', response.content.decode())
        self.assertEqual(self.register().status_code, 400)
        self.assertEqual(self.register('mismatch', password_confirm='other').status_code, 400)
        self.assertEqual(self.register('weak', password='123', password_confirm='123').status_code, 400)

    @override_settings(ADMIN_REGISTRATION_CODE='')
    def test_closed_registration(self):
        self.assertEqual(self.register().status_code, 400)
        self.assertFalse(User.objects.exists())

    def test_legacy_account_cannot_authenticate_even_with_valid_password(self):
        user = User.objects.create_user('legacy', password=self.password, role='learner')
        self.assertEqual(self.signin('legacy').status_code, 401)
        self.assertContains(self.client.post('/staff/login/', {'username': 'legacy', 'password': self.password}), '올바른')
        self.client.force_login(user, backend='accounts.backends.AdminBackend')
        self.assertEqual(self.client.get('/api/admin/summary').status_code, 401)
        self.client.force_login(user, backend='django.contrib.auth.backends.ModelBackend')
        self.assertEqual(self.client.get('/api/auth/me').status_code, 401)

    def test_login_inactive_logout_replay_and_isolation(self):
        self.register()
        self.register('operatorB')
        self.assertEqual(self.signin(password='wrong').status_code, 401)
        self.assertEqual(self.signin().status_code, 200)
        other = Client()
        self.signin('operatorB', client=other)
        self.assertNotEqual(self.client.get('/api/auth/me').json()['user']['user_id'], other.get('/api/auth/me').json()['user']['user_id'])
        old_cookie = self.client.cookies['sessionid'].value
        self.assertEqual(self.client.post('/api/auth/logout', '{}', content_type='application/json').status_code, 200)
        self.client.cookies['sessionid'] = old_cookie
        self.assertEqual(self.client.get('/api/auth/me').status_code, 401)
        self.assertEqual(other.get('/api/auth/me').status_code, 200)
        User.objects.filter(username='operatorB').update(is_active=False)
        self.assertEqual(other.get('/api/auth/me').status_code, 401)
        self.assertEqual(self.signin('operatorB').status_code, 401)

    def test_web_flow_and_csrf(self):
        data = {'username': 'webadmin', 'display_name': '웹 운영자', 'password1': self.password,
                'password2': self.password, 'invitation_code': 'test-invite-only'}
        self.assertRedirects(self.client.post('/staff/register/', data), '/staff/login/')
        client = Client(enforce_csrf_checks=True)
        token = client.get('/api/auth/csrf').json()['csrf_token']
        response = client.post('/api/auth/login', json.dumps({'login_id': 'webadmin', 'password': self.password}), content_type='application/json', HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code, 200)
        dashboard = client.get('/staff/')
        self.assertEqual(dashboard.status_code, 200)
        self.assertTemplateUsed(dashboard, 'telemetry/dashboard.html')
        self.assertEqual(dashboard.wsgi_request.user.username, 'webadmin')
        self.assertEqual(client.post('/api/auth/logout', '{}', content_type='application/json').status_code, 403)
        self.assertEqual(client.post('/api/auth/logout', '{}', content_type='application/json', HTTP_X_CSRFTOKEN=response.json()['csrf_token']).status_code, 200)

    def test_superuser_and_method_validation(self):
        user = User.objects.create_superuser('rootadmin', password=self.password, display_name='관리자')
        self.assertEqual(user.role, 'admin')
        self.assertEqual(self.signin('rootadmin').status_code, 200)
        self.assertEqual(self.client.get('/api/auth/logout').status_code, 405)
        self.assertEqual(self.client.post('/api/auth/login', '[]', content_type='application/json').status_code, 400)
        self.assertEqual(self.client.post('/api/auth/login', {}).status_code, 415)
