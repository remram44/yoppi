import logging
from optparse import make_option
from django.core.management.base import LabelCommand, CommandError, BaseCommand
from django.utils.encoding import smart_str
from django.utils.translation import pgettext_lazy, pgettext, ugettext, gettext_lazy
from yoppi.ftp.models import FtpServer
from yoppi.indexer.app import ServerAlreadyIndexing, get_project_indexer
from yoppi.indexer.management.commands import setup_logging


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--all',
            action='store_true',
            dest='all',
            default=False,
            help=pgettext_lazy("'index' command", "Index all known ftps")),
        )

    args = pgettext_lazy("args for 'index' command",
                         "<server_address> [server_address [...]]")
    help = pgettext_lazy("help for 'index' command",
                         "(re-)index the specified FTP server")
    label = pgettext_lazy("labels received by the 'index' command",
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
        logger.warn(pgettext("indexing in progress from 'index' command",
                             "Indexing '%s'..."), address)
        try:
            nb_files, total_size, to_insert, to_delete = \
                    self.indexer.index(address)
            logger.warn(gettext_lazy("%(nb_files)d files found on %(address)s, "
                                      "%(total_size)d b"),
                        dict(nb_files=nb_files, address=address,
                             total_size=total_size))
            logger.info(gettext_lazy("%(ins)d insertions, %(dele)d deletions"),
                        dict(ins=len(to_insert), dele=len(to_delete)))
        except ServerAlreadyIndexing as e:
            raise CommandError(
                    ugettext("%s is already being indexed") % address, e)
        except (ValueError, IOError) as e:
            raise CommandError("%s: %s" % (e.__class__.__name__, e))
