import contextlib
from yoppi.ftp.models import FtpServer, File
from iptools import IP, IPRange, parse_ip_ranges
from walk_ftp import walk_ftp
from yoppi import settings

from django.db import IntegrityError
from django.utils import timezone

import socket
from exceptions import IOError
import ftplib
from sys import stdout

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
            SEARCH_ON_USER=True, USER_IN_RANGE_ONLY=True,
            TIMEOUT=2):
        self.ip_ranges = parse_ip_ranges(IP_RANGES)
        self.scan_delay = SCAN_DELAY
        self.index_delay = INDEX_DELAY
        self.search_on_user = SEARCH_ON_USER
        self.user_in_range_only = USER_IN_RANGE_ONLY
        self.timeout = TIMEOUT

    def _defaultServerName(self, address):
        try:
            names = socket.gethostbyaddr(address)
            return names[0]
        except socket.herror:
            return ''

    # Scan an IP range
    def scan(self, min_ip, max_ip, verbose=1):
        range = IPRange(min_ip, max_ip)
        found = 0
        for ip in range:
            address = str(ip)
            try:
                ftp = ftplib.FTP(timeout=self.timeout)
                ftp.connect(address)
                ftp.close()
            # Server offline
            except IOError:
                try:
                    server = FtpServer.objects.get(address=address)
                    if verbose != 0:
                        name = server.display_name()
                        if not server.online and verbose >= 2:
                            stdout.write("%s is still offline\n" % name)
                        elif server.online and verbose >= 1:
                            stdout.write("%s is now offline\n" % name)
                    server.online = False
                    server.save()
                except FtpServer.DoesNotExist:
                    if verbose >= 3:
                        stdout.write("%s didn't respond\n" % address)
            # Server online
            else:
                found += 1
                try:
                    server = FtpServer.objects.get(address=address)
                    if verbose != 0:
                        name = server.display_name()
                        if server.online and verbose >= 2:
                            stdout.write("%s is still online\n" % name)
                        elif not server.online and verbose >= 1:
                            stdout.write("%s is now online\n" % name)
                    server.online = True
                    server.last_online = timezone.now()
                    server.save()
                except FtpServer.DoesNotExist:
                    if verbose >= 1:
                        stdout.write("discovered new server at %s\n" % address)
                    server = FtpServer(
                        address=address, name=self._defaultServerName(address),
                        online=True, last_online=timezone.now())
                    server.save()
        return found

    # Index a server
    def index(self, address):
        # 'address' must be a valid IP address
        if not isinstance(address, IP):
            address = IP(address)
        address = str(address)

        try:
            ftp = ftplib.FTP(timeout=self.timeout)
            ftp.connect(address)
        # Server offline
        except IOError:
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
            ftp.sendcmd('OPTS UTF8 ON')

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
            return nb_files, total_size, to_insert, to_delete

    def run(self, args):
        pass
