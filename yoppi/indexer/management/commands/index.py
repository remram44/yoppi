import logging
from optparse import make_option
from django.core.management.base import CommandError, BaseCommand
from django.utils.encoding import smart_str
from django.utils.translation import pgettext_lazy, ugettext
from yoppi.ftp.models import FtpServer
from yoppi.indexer.app import ServerAlreadyIndexing, get_project_indexer
from yoppi.indexer.management.commands import setup_logging, fixed_pgettext_lazy


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--all',
            action='store_true',
            dest='all',
            default=False,
            help=fixed_pgettext_lazy("'index' command", "Index all known ftps")),
        )

    args = fixed_pgettext_lazy("args for 'index' command",
                         "<server_address> [server_address [...]]")
    help = fixed_pgettext_lazy("help for 'index' command",
                         "(re-)index the specified FTP server")
    label = fixed_pgettext_lazy("labels received by the 'index' command",
                          "address")

    def __init__(self):
        super(Command, self).__init__()
        self.indexer = get_project_indexer()

    def handle(self, *args, **options):
        setup_logging(options['verbosity'])

        if options['all']:
            for address_in_tuple in FtpServer.objects.values_list('address'):
                try:
                    self.index(address_in_tuple[0])
                except CommandError as e:
                    self.stderr.write(smart_str(self.style.ERROR(
                            ugettext('Error: %s\n' % e))))
        else:
            for address in args:
                self.index(address)

    def index(self, address):
        try:
            self.indexer.index(address)
        except ServerAlreadyIndexing as e:
            raise CommandError(
                    ugettext("%s is already being indexed") % address, e)
        except (ValueError, IOError) as e:
            raise CommandError("%s: %s" % (e.__class__.__name__, e))
