from __future__ import unicode_literals

from django.conf import settings as django_settings
from django.core.management.base import NoArgsCommand
from django.utils.translation import ugettext_lazy

from yoppi.indexer.app import Indexer
from yoppi.indexer.management.commands import setup_logging


try:
    settings = django_settings.INDEXER_SETTINGS
except KeyError:
    settings = {}


class Command(NoArgsCommand):
    help = ugettext_lazy("help for 'cron' command",
                         "called regularly to perform the actions configured "
                         "in settings.py")

    def handle(self, *args, **options):
        setup_logging(options['verbosity'])

        indexer = Indexer(**settings)

        indexer.run(args)
