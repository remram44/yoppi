from yoppi.ftp.models import FtpServer
from iptools import IPRange
from walk_ftp import walk_ftp

from django.db import IntegrityError
from django.utils import timezone

from exceptions import IOError
from ftplib import FTP
from sys import stdout


class ServerIndexingLock:
    def __init__(self, address):
        self.address = address

    def __enter__(self):
        # Try to create a FtpServer
        try:
            self.server = FtpServer(
                    address=self.address,
                    online=True, last_online=timezone.now(),
                    indexing=timezone.now())
            self.server.save(force_insert=True)
            return self.server
        # It already exists -- try to update it
        except IntegrityError:
            self.server = None
            # Try to lock it
            if (FtpServer.objects.filter(indexing=None, address=self.address)
                    .update(indexing=timezone.now()) == 0):
                return None
            else:
                self.server = FtpServer.objects.get(address=self.address)
                self.server.online = True
                self.server.last_online = timezone.now()
                self.server.indexing = timezone.now()
                self.server.save()
                return self.server

    def __exit__(self, type, value, traceback):
        if self.server != None:
            self.server.indexing = None
            self.server.save()


class Indexer:
    def __init__(
            self,
            IP_RANGES=(),
            SCAN_DELAY=30*60, INDEX_DELAY=2*60*60,
            SEARCH_ON_USER=True, USER_IN_RANGE_ONLY=True,
            TIMEOUT=2):
        self.ip_ranges = IP_RANGES
        self.scan_delay = SCAN_DELAY
        self.index_delay = INDEX_DELAY
        self.search_on_user = SEARCH_ON_USER
        self.user_in_range_only = USER_IN_RANGE_ONLY
        self.timeout = TIMEOUT

    # Scan an IP range
    def scan(self, min_ip, max_ip, verbose=1):
        range = IPRange(min_ip, max_ip)
        found = 0
        for ip in range:
            address = str(ip)
            try:
                ftp = FTP(timeout=self.timeout)
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
                        address=address,
                        online=True, last_online=timezone.now())
                    server.save()
        return found            

    # Index a server
    def index(self, address, verbose=1):
        try:
            ftp = FTP(timeout=self.timeout)
            ftp.connect(address)
        # Server offline
        except IOError:
            try:
                server = FtpServer.objects.get(address=address)
                if server.online:
                    server.online = False
                    server.save()
            except FtpServer.DoesNotExist:
                if verbose >= 1:
                    stdout.write("couldn't connect to %s\n" % address)
            return False

        with ServerIndexingLock(address) as server:
            if server == None:
                if verbose >= 1:
                    stdout.write("%s already being indexed\n" % address)
                return False

            try:
                ftp.login()
                nb_files, total_size = walk_ftp(server, ftp)
                ftp.close()
                if verbose >= 1:
                    stdout.write("%d files found on %s, %d b\n" %
                            (nb_files, address, total_size))
                return True
            except IOError as e:
                stdout.write("I/O error!\n%s\n" % e)
                return False

    def run(self, args):
        pass
