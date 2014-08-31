from __future__ import unicode_literals

from optparse import make_option

from django.core.management.base import BaseCommand
from django.utils.translation import ugettext_lazy

from yoppi.indexer.app import get_project_indexer
from yoppi.indexer.management.commands import setup_logging

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--all',
            action='store_true',
            dest='all',
            default=False,
            help=ugettext_lazy("'checkstatus' command",
                               "Check all known servers")),
        )
    args = ugettext_lazy("args for 'checkstatus' command",
                         "<server_address> [server_address [...]]")
    help = ugettext_lazy("help for 'checkstatus' command",
                         "Check the availability of all known servers")

    def handle(self, *args, **options):
        setup_logging(options['verbosity'])
        indexer = get_project_indexer()

        if options['all']:
            indexer.check_all_statuses()
        else:
            indexer.check_statuses(args)
