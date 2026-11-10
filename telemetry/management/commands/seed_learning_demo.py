from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    help = 'Create a small structured MongoDB learning demo.'
    def handle(self, *args, **options):
        call_command('seed_observatory', players=6, visits=3, stdout=self.stdout)
