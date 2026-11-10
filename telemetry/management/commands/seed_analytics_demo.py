import uuid
from django.core.management.base import BaseCommand
from django.core.management import call_command

NAMESPACE = uuid.UUID('3b5d89d4-c510-4b52-aef2-9e914167941a')


def stable(value):
    return uuid.uuid5(NAMESPACE, value)


class Command(BaseCommand):
    help = 'Create a small MongoDB analytics demo.'
    def handle(self, *args, **options):
        call_command('seed_observatory', players=6, visits=6, stdout=self.stdout)
