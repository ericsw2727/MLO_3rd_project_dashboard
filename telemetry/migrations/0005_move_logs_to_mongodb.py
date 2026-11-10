"""Copy and verify every log before removing SQL tables. No implicit data loss."""
from django.db import migrations


def move_logs(apps, schema_editor):
    from telemetry.mongo import database, document, initialize_indexes
    from telemetry.metadata import validate_metadata
    from pymongo.errors import DuplicateKeyError
    initialize_indexes()
    db = database()
    names = ('PlaySession', 'LearningTask', 'TaskRun', 'SolveAttempt', 'BehaviorEvent')
    for name in names:
        model = apps.get_model('telemetry', name)
        target = db[model._meta.db_table]
        for instance in model.objects.using(schema_editor.connection.alias).iterator():
            data = document(instance)
            if name == 'BehaviorEvent':
                for field in ('payload', 'state_before', 'state_after'):
                    validate_metadata(data[field])
            try:
                target.update_one({'_id': data['_id']}, {'$setOnInsert': data}, upsert=True)
            except DuplicateKeyError:
                raise RuntimeError(f'{name}: MongoDB identifier conflict; SQL tables preserved.') from None
            if target.find_one({'_id': data['_id']}) != data:
                raise RuntimeError(f'{name}: copy verification failed; SQL tables preserved.')
    # All records in all collections are verified before any SQL table is dropped.


def prevent_unsafe_reverse(apps, schema_editor):
    raise RuntimeError('MongoDB logs require an explicit export before restoring SQL storage.')


class Migration(migrations.Migration):
    atomic = False
    dependencies = [('telemetry', '0004_alter_behaviorevent_table_alter_learningtask_table_and_more')]
    operations = [
        migrations.RunPython(move_logs, migrations.RunPython.noop),
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.DeleteModel(name='BehaviorEvent'),
                migrations.DeleteModel(name='SolveAttempt'),
                migrations.DeleteModel(name='TaskRun'),
                migrations.DeleteModel(name='LearningTask'),
                migrations.DeleteModel(name='PlaySession'),
            ],
            state_operations=[migrations.AlterModelOptions(name=name, options={
                'managed': False, **({'ordering': ['occurred_at', 'sequence', 'id']} if name == 'behaviorevent' else {})}) for name in
                              ('behaviorevent', 'solveattempt', 'taskrun', 'learningtask', 'playsession')],
        ),
        # This reverse guard runs before reverse DDL could create empty SQL tables.
        migrations.RunPython(migrations.RunPython.noop, prevent_unsafe_reverse),
    ]
