from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User
from django import forms
from django.conf import settings
from django.utils.crypto import constant_time_compare

class RegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'display_name')
        labels = {'username': '아이디', 'display_name': '표시 이름'}

class LoginForm(AuthenticationForm):
    pass

class AdminRegisterForm(RegisterForm):
    invitation_code = forms.CharField(label='관리자 초대 코드', widget=forms.PasswordInput,
                                     help_text='운영자가 전달한 초대 코드가 필요합니다.')

    def clean_invitation_code(self):
        value = self.cleaned_data['invitation_code']
        expected = settings.ADMIN_REGISTRATION_CODE
        if not expected or not constant_time_compare(value, expected):
            raise forms.ValidationError('유효한 관리자 초대 코드가 필요합니다.')
        return value

class AdminLoginForm(LoginForm):
    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if user.role != 'admin':
            raise forms.ValidationError('관리자 계정으로 로그인해 주세요.', code='not_admin')
