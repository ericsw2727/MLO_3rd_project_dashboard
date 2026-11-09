from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    help = 'Compatibility alias for seed_analytics_demo. Does not create login accounts.'

    def handle(self, *args, **options):
        call_command('seed_analytics_demo', stdout=self.stdout)
