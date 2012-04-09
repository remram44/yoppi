from django.core.management.base import BaseCommand, CommandError
from yoppi.indexer.app import Indexer
from yoppi.ftp.models import FtpServer

from django.conf import settings as django_settings


try:
    settings = django_settings.INDEXER_SETTINGS
except KeyError:
    settings = {}


class Command(BaseCommand):
    args = '<first IP> [last IP]'
    help = 'scan the specified IP range to detect FTP servers'

    def handle(self, *args, **options):
        indexer = Indexer(**settings)

        try:
            if len(args) == 1:
                indexer.scan(args[0], args[0])
            elif len(args) == 2:
                indexer.scan(args[0], args[1])
            else:
                raise CommandError("Expected 2 parameters, got %d" % len(args))
        except ValueError as e:
            raise CommandError("%s: %s" % (e.__class__.__name__, e))
