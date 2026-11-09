from django.db import IntegrityError, transaction
from .forms import AdminRegisterForm

def register(data):
    form = AdminRegisterForm(data)
    if form.is_valid():
        try:
            with transaction.atomic():
                user = form.save(commit=False)
                user.role = 'admin'
                user.save()
            return user, form
        except IntegrityError:
            form.add_error('username', '이미 사용 중인 아이디입니다.')
    return None, form

def user_data(user):
    return {'user_id': str(user.pk), 'login_id': user.username, 'display_name': user.display_name,
            'role': user.role, 'is_active': user.is_active, 'created_at': user.date_joined.isoformat(),
            'updated_at': user.updated_at.isoformat()}
