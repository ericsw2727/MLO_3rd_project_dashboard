from django.db import migrations


def describe_tables(apps, schema_editor):
    if schema_editor.connection.vendor != 'mysql':
        return
    descriptions = {
        'admin_group_memberships': '관리자가 어떤 권한 그룹에 속하는지 연결',
        'admin_permission_assignments': '관리자에게 직접 부여한 개별 권한',
        'auth_group': '관리자 권한 그룹 정의. 게임 회원 그룹이 아님',
        'auth_group_permissions': '권한 그룹과 허용 작업의 연결',
        'auth_permission': 'Django에서 사용하는 조회·추가·수정·삭제 권한 목록',
        'django_content_type': 'Django 모델 종류 목록. 권한 시스템에서 사용',
        'django_migrations': 'DB 구조 변경 적용 이력. 회원 또는 게임 기록이 아님',
        'django_session': '관리자 웹 로그인 유지 정보. 게임 플레이 세션이 아님',
    }
    with schema_editor.connection.cursor() as cursor:
        for table, description in descriptions.items():
            cursor.execute(f'ALTER TABLE {schema_editor.quote_name(table)} COMMENT = %s', [description])


class Migration(migrations.Migration):
    dependencies = [('accounts', '0004_alter_user_table_comment_alter_user_date_joined_and_more')]
    operations = [migrations.RunPython(describe_tables, migrations.RunPython.noop)]
