import contextlib
import logging
from yoppi.ftp.models import FtpServer, File
from iptools import IP, IPRange, parse_ip_ranges
from walk_ftp import walk_ftp
from yoppi import settings
from models import IndexerParameter

from django.db import IntegrityError
from django.utils import timezone
from django.utils.translation import ugettext, pgettext, gettext_lazy
from django.conf import settings as django_settings

from itertools import izip
import socket
from exceptions import IOError
import ftplib


logger = logging.getLogger(__name__)


class ServerAlreadyIndexing(Exception):
    pass


@contextlib.contextmanager
def ServerIndexingLock(address, name=None):
    # Try to create a FtpServer
    try:
        server = FtpServer(
                address=address, name=name,
                online=True, last_online=timezone.now(),
                indexing=timezone.now())
        server.save(force_insert=True)
    # It already exists -- try to update it
    except IntegrityError:
        # Try to lock it
        if (FtpServer.objects.filter(indexing=None, address=address)
                .update(indexing=timezone.now()) == 0):
            raise ServerAlreadyIndexing(address)
        else:
            server = FtpServer.objects.get(address=address)
            server.online = True
            server.last_online = timezone.now()
            server.indexing = timezone.now()
            server.save()

    try:
        yield server
    finally:
        server.indexing = None
        server.save()


def ftp_online(address, timeout):
    try:
        ftp = ftplib.FTP(timeout=timeout)
        ftp.connect(address)
        ftp.close()
        return True
    except ftplib.all_errors:
        return False

def safe_bulk_create(to_insert):
    try:
        BULK_SIZE = settings.DATABASES['default']['BULK_SIZE']
    except KeyError:
        if 'sqlite' in settings.DATABASES['default']['ENGINE']:
            BULK_SIZE = 100
        else:
            BULK_SIZE = 10000

    if BULK_SIZE is not None and BULK_SIZE > 0:
        for i in range(0, len(to_insert), BULK_SIZE):
            File.objects.bulk_create(to_insert[i:i + BULK_SIZE])
    else:
        File.objects.bulk_create(to_insert)


class Indexer:
    def __init__(
            self,
            IP_RANGES=(),
            SCAN_DELAY=30*60, INDEX_DELAY=2*60*60,
            SCAN_COUNT=200, INDEX_COUNT=10,
            PRUNE_FTP_TIME=7*24*3600,
            SEARCH_ON_USER=True, USER_IN_RANGE_ONLY=True,
            TIMEOUT=2):
        self.ip_ranges = parse_ip_ranges(IP_RANGES)
        self.scan_delay = SCAN_DELAY
        self.index_delay = INDEX_DELAY
        self.scan_count = SCAN_COUNT
        self.index_count = INDEX_COUNT
        self.prune_ftp_time = PRUNE_FTP_TIME
        self.search_on_user = SEARCH_ON_USER
        self.user_in_range_only = USER_IN_RANGE_ONLY
        self.timeout = TIMEOUT

    def _defaultServerName(self, address):
        try:
            names = socket.gethostbyaddr(address)
            return names[0]
        except socket.herror:
            return ''

    def _scan_address(self, address, ftp_object=None):
        if ftp_online(address, self.timeout):
            try:
                if not ftp_object:
                    ftp_object = FtpServer.objects.get(address=address)
                if logger.isEnabledFor(logging.WARN):
                    name = ftp_object.display_name()
                    if ftp_object.online:
                        logging.info(ugettext("%s is still online"), name)
                    else:
                        logging.warn(ugettext("%s is now online"), name)
                ftp_object.online = True
                ftp_object.last_online = timezone.now()
                ftp_object.save()
            except FtpServer.DoesNotExist:
                logger.warn(ugettext("discovered new server at %s\n"),
                            address)
                server = FtpServer(
                    address=address, name=self._defaultServerName(address),
                    online=True, last_online=timezone.now())
                server.save()
            return True
        else:
            try:
                if not ftp_object:
                    ftp_object = FtpServer.objects.get(address=address)
                if logger.isEnabledFor(logging.WARN):
                    name = ftp_object.display_name()
                    if not ftp_object.online:
                        logger.info(ugettext("%s is still offline"), name)
                    else:
                        logger.warn(ugettext("%s is now offline"), name)
                ftp_object.online = False
                ftp_object.save()
            except FtpServer.DoesNotExist:
                logger.debug(ugettext("%s didn't respond"), address)
            return False

    # Scan an IP range
    def scan(self, min_ip, max_ip):
        return sum(self._scan_address(str(ip))
            for ip in IPRange(min_ip, max_ip))

    def watchdog(self):
        """Check if the known ftps are online"""
        for ftp in FtpServer.objects.all():
            self._scan_address(ftp.address, ftp)

    # Index a server
    def index(self, address):
        logger.warn(pgettext("indexing in progress from 'index' command",
                             "Indexing '%s'..."), address)

        # 'address' must be a valid IP address
        if not isinstance(address, IP):
            address = IP(address)
        address = str(address)

        try:
            ftp = ftplib.FTP(timeout=self.timeout)
            ftp.connect(address)
        # Server offline
        except ftplib.all_errors:
            try:
                server = FtpServer.objects.get(address=address)
                if server.online:
                    server.online = False
                    server.save()
            except FtpServer.DoesNotExist:
                pass
            raise

        name = self._defaultServerName(address)

        with ServerIndexingLock(address, name) as server:
            ftp.login()
            try:
                ftp.sendcmd('OPTS UTF8 ON')
            except ftplib.error_perm:
                logger.warn(ugettext("server %s doesn't seem to handle unicode. "
                                     "Brace yourselves."), address)
                pass

            # Fetch all the files currently known
            files = dict((f.fullpath(), f) for f in File.objects.filter(server=server))

            # Recursively walk the FTP
            to_insert, to_delete, nb_files, total_size = \
                    walk_ftp(server, ftp, files)
            # The file that were not found need to be deleted as well
            to_delete.extend(f.id for f in files.itervalues())

            # Update the files in the database
            File.objects.filter(id__in=to_delete).delete()

            safe_bulk_create(to_insert)

            # Update the server
            server.size = total_size
            # It will get save()'d when we exit the 'with' block

            ftp.close()
            logger.warn(gettext_lazy("%(nb_files)d files found on %(address)s, "
                                     "%(total_size)d b"),
                        dict(nb_files=nb_files, address=address,
                             total_size=total_size))
            logger.info(gettext_lazy("%(ins)d insertions, %(dele)d deletions"),
                        dict(ins=len(to_insert), dele=len(to_delete)))
            return nb_files, total_size, to_insert, to_delete

    def getConfig(self, name):
        try:
            p = IndexerParameter.objects.get(name=name)
            return p.value
        except IndexerParameter.DoesNotExist:
            return None

    def setConfig(self, name, value):
        p = IndexerParameter(name, value)
        p.save() # Overwrites any existing value

    def run(self, args):
        # Scan the configured number of addresses (or all the addresses in the
        # configured range) from the last scanned address
        # Uses: SCAN_DELAY, SCAN_COUNT
        last_scanned_ip = self.getConfig('last_scanned_ip')
        if (last_scanned_ip is None or
                not self.ip_ranges.contains(last_scanned_ip)):
            last_scanned_ip = self.ip_ranges.first()

        try:
            for i, ip in izip(xrange(1, self.scan_count),
                              self.ip_ranges.loop_iter_from(last_scanned_ip)):
                self._scan_address(ip)
                last_scanned_ip = ip
        except KeyboardInterrupt:
            pass # Stop here

        self.setConfig('last_scanned_ip', str(last_scanned_ip))

        # TODO : Check the known FTPs (all of them?)

        # TODO : Remove the old FTPs (that haven't been online in a long time)
        # Uses: PRUNE_FTP_TIME

        # TODO : Index the FTPs that have been indexed last
        # Uses: INDEX_DELAY, INDEX_COUNT
        for ftp in FtpServer.objects.all():
            try:
                self.index(ftp.address)
            except socket.error:
                logger.info('%s is offline, not indexing.', ftp.address)


def get_project_indexer():
    return Indexer(**getattr(django_settings, 'INDEXER_SETTINGS', {}))
