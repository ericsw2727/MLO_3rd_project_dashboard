import json
from django.core.exceptions import ValidationError

def validate_metadata(value):
    if len(json.dumps(value, ensure_ascii=False).encode('utf-8')) > 16384:
        raise ValidationError('상태·추가 데이터는 각각 16KB 이하여야 합니다.')
    forbidden = {'password', 'password_hash', 'authorization', 'session_cookie', 'secret_key', 'admin_registration_code'}
    def walk(item):
        if isinstance(item, dict):
            if any(str(key).lower() in forbidden for key in item):
                raise ValidationError('비밀값을 행동 로그에 저장할 수 없습니다.')
            for nested in item.values():
                walk(nested)
        elif isinstance(item, list):
            for nested in item:
                walk(nested)
    walk(value)


