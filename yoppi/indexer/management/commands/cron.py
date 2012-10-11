from django.core.management.base import NoArgsCommand, CommandError
from yoppi.indexer.app import Indexer
from yoppi.ftp.models import FtpServer

from django.conf import settings as django_settings


try:
    settings = django_settings.INDEXER_SETTINGS
except KeyError:
    settings = {}


class Command(NoArgsCommand):
    help = 'called regularly to perform the actions configured in settings.py'

    def handle(self, *args, **options):
        indexer = Indexer(**settings)

        indexer.run(args)
