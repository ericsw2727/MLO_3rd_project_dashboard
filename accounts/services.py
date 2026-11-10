from django.db import IntegrityError, transaction
from .forms import AdminRegisterForm

def register_admin_account(registration_data):
    registration_form = AdminRegisterForm(registration_data)
    if registration_form.is_valid():
        try:
            with transaction.atomic():
                admin_account = registration_form.save(commit=False)
                admin_account.role = 'admin'
                admin_account.save()
            return admin_account, registration_form
        except IntegrityError:
            registration_form.add_error('username', '이미 사용 중인 아이디입니다.')
    return None, registration_form

def admin_account_data(admin_account):
    return {'user_id': str(admin_account.pk), 'login_id': admin_account.username, 'display_name': admin_account.display_name,
            'role': admin_account.role, 'is_active': admin_account.is_active, 'created_at': admin_account.date_joined.isoformat(),
            'updated_at': admin_account.updated_at.isoformat()}
