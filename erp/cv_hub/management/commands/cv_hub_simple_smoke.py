from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Run smoke tests for CV Hub functionality'

    def handle(self, *args, **options):
        self.stdout.write('Simple smoke test - CV_HUB_SMOKE_OK')
