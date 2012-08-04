from django.core.management.base import NoArgsCommand
from yoppi.indexer.app import get_project_indexer
from yoppi.indexer.management.commands import setup_logging

class Command(NoArgsCommand):
    help = 'Check if the known ftps are online'

    def handle_noargs(self, **options):
        setup_logging(options['verbosity'])
        get_project_indexer().watchdog()
