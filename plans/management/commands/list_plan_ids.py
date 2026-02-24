from django.core.management.base import BaseCommand
from plans.models import Plan

class Command(BaseCommand):
    help = 'List all plan IDs in the database'

    def handle(self, *args, **kwargs):
        for plan in Plan.objects.all():
            self.stdout.write(str(plan.id))
