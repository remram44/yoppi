from optparse import make_option
from django.core.management.base import LabelCommand, CommandError, BaseCommand
from django.utils.encoding import smart_str
from django.utils.translation import pgettext_lazy, pgettext, ugettext
from yoppi.ftp.models import FtpServer
from yoppi.indexer.app import Indexer, ServerAlreadyIndexing

from django.conf import settings as django_settings


try:
    settings = django_settings.INDEXER_SETTINGS
except KeyError:
    settings = {}


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
        self.indexer = Indexer(**settings)

    def handle(self, *args, **options):
        verbosity = options.get('verbosity', False)
        if options['all']:
            for address_in_tuple in FtpServer.objects.values_list('address'):
                try:
                    self.index(address_in_tuple[0], verbosity=verbosity)
                except CommandError as e:
                    self.stderr.write(smart_str(self.style.ERROR(
                            ugettext('Error: %s\n' % e))))
        else:
            for address in args:
                self.index(address, verbosity=verbosity)

    def index(self, address, verbosity):
        print pgettext("indexing in progress from 'index' command",
                       "Indexing '%s'..." % address)
        try:
            nb_files, total_size, to_insert, to_delete = \
                    self.indexer.index(address)
            if verbosity >= 1:
                print (ugettext("%(nb_files)d files found on %(address)s, "
                        "%(total_size)d b") %
                        dict(nb_files=nb_files, address=address,
                             total_size=total_size))
            if verbosity >= 2:
                print (ugettext("%(ins)d insertions, %(dele)d deletions") %
                        dict(ins=len(to_insert), dele=len(to_delete)))
        except ServerAlreadyIndexing as e:
            raise CommandError(
                    ugettext("%s is already being indexed") % address, e)
        except (ValueError, IOError) as e:
            raise CommandError("%s: %s" % (e.__class__.__name__, e))
