from django.db import migrations


def preserve_players(apps, schema_editor):
    User = apps.get_model('accounts', 'User')
    Player = apps.get_model('telemetry', 'Player')
    alias = schema_editor.connection.alias
    for user in User.objects.using(alias).filter(role='learner').iterator():
        Player.objects.using(alias).get_or_create(id=user.pk, defaults={
            'external_id': f'legacy:{user.pk}', 'display_name': user.display_name or user.username,
            'source': 'demo' if user.username.startswith('demo_') else 'live'})


class Migration(migrations.Migration):
    dependencies = [('telemetry', '0001_initial'), ('accounts', '0002_alter_user_role')]
    # Reverse intentionally preserves data; auth accounts themselves remain untouched.
    operations = [migrations.RunPython(preserve_players, migrations.RunPython.noop)]
