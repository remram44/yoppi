from optparse import make_option
from django.core.management.base import LabelCommand, CommandError, BaseCommand
from django.utils.encoding import smart_str
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
            help='Index all known ftps'),
        )

    args = '<server_address> [server_address [...]]'
    help = '(re-)index the specified FTP server'
    label = 'address'

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
                    self.stderr.write(smart_str(self.style.ERROR('Error: %s\n' % e)))
        else:
            for address in args:
                self.index(address, verbosity=verbosity)

    def index(self, address, verbosity):
        print 'Indexing "%s"...' % address
        try:
            nb_files, total_size, to_insert, to_delete = self.indexer.index(address)
            if verbosity >= 1:
                print "%d files found on %s, %d b" % (nb_files, address, total_size)
            if verbosity >= 2:
                print "%d insertions, %s deletions" % (len(to_insert), len(to_delete))
        except ServerAlreadyIndexing as e:
            raise CommandError("%s is already being indexed", e)
        except (ValueError, IOError) as e:
            raise CommandError("%s: %s" % (e.__class__.__name__, e))
