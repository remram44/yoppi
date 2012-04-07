from ftp.models import FtpServer
from models import IndexerParam
from iptools import IPRange

from exceptions import IOError
from datetime import datetime
from ftplib import FTP
from sys import stdout


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
    def scan(self, min_ip, max_ip, verbose=3):
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
                    server.last_online = datetime.now()
                    server.save()
                except FtpServer.DoesNotExist:
                    if verbose >= 1:
                        stdout.write("discovered new server at %s\n" % address)
                    server = FtpServer(
                        address=address,
                        online=True, last_online=datetime.now())
                    server.save()
        return found

    def _index_rec(self, address, ftp, path):
        files = ftp.nlst(path)
        for file in files:
            print file

    # Index a server
    def index(self, address):
        try:
            ftp = FTP(timeout=self.timeout)
            ftp.connect(address)
            ftp.login()
            self._index_rec(address, ftp, "/")
            ftp.close()
            return True
        except IOError:
            return False

    def run(self, args):
        pass
