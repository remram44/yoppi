from django.core.management.base import BaseCommand, CommandError
from django.utils.translation import pgettext_lazy, ugettext
from yoppi.indexer.app import get_project_indexer
from yoppi.indexer.management.commands import setup_logging


class Command(BaseCommand):
    args = pgettext_lazy("args for 'scan' command",
                         "<first IP> [last IP]")
    help = pgettext_lazy("help for 'scan' command",
                         "scan the specified IP range to detect FTP servers")

    def handle(self, *args, **options):
        setup_logging(options['verbosity'])
        indexer = get_project_indexer()

        try:
            if len(args) == 1:
                indexer.scan(args[0], args[0])
            elif len(args) == 2:
                indexer.scan(args[0], args[1])
            else:
                raise CommandError(
                        ugettext("Expected 2 parameters, got %d") % len(args))
        except ValueError as e:
            raise CommandError("%s: %s" % (e.__class__.__name__, e))
