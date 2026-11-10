from django.core.management.base import BaseCommand
from telemetry.mongo import database, initialize_indexes, LOG_MODELS


class Command(BaseCommand):
    help = 'Check MongoDB connectivity and create required log indexes.'

    def handle(self, *args, **options):
        db = database()
        db.command('ping')
        initialize_indexes()
        for model in LOG_MODELS:
            self.stdout.write(f'{model._meta.db_table}: {db[model._meta.db_table].count_documents({})}')
        self.stdout.write(self.style.SUCCESS('MongoDB ready.'))
