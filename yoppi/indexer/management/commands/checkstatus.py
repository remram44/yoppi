from optparse import make_option

from django.core.management.base import BaseCommand
from django.utils.translation import pgettext_lazy

from yoppi.indexer.app import get_project_indexer
from yoppi.indexer.management.commands import setup_logging

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--all',
            action='store_true',
            dest='all',
            default=False,
            help=pgettext_lazy(u"'checkstatus' command",
                               u"Check all known servers")),
        )
    args = pgettext_lazy(u"args for 'checkstatus' command",
                         u"<server_address> [server_address [...]]")
    help = pgettext_lazy(u"help for 'checkstatus' command",
                         u"Check the availability of all known servers")

    def handle(self, *args, **options):
        setup_logging(options['verbosity'])
        indexer = get_project_indexer()

        if options['all']:
            indexer.check_all_statuses()
        else:
            indexer.check_statuses(args)
