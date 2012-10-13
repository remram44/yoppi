from django.conf import settings as django_settings
from django.core.management.base import NoArgsCommand, CommandError
from django.utils.translation import pgettext_lazy

from yoppi.indexer.app import Indexer
from yoppi.indexer.management.commands import setup_logging
from yoppi.ftp.models import FtpServer


try:
    settings = django_settings.INDEXER_SETTINGS
except KeyError:
    settings = {}


class Command(NoArgsCommand):
    help = pgettext_lazy(u"help for 'cron' command",
                         u"called regularly to perform the actions configured "
                         "in settings.py")

    def handle(self, *args, **options):
        setup_logging(options['verbosity'])

        indexer = Indexer(**settings)

        indexer.run(args)
