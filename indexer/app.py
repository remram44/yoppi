from ftp.models import FtpServer
from indexer.models import IndexerParam


class Indexer:
    def __init__(
            self,
            IP_RANGES=(),
            SCAN_DELAY=30*60, INDEX_DELAY=2*60*60,
            SEARCH_ON_USER=True, USER_IN_RANGE_ONLY=True):
        pass

    # Scan an IP range
    def scan(self, min_ip, max_ip):
        pass

    # Index a server
    def index(self, address):
        pass

    def run(self, args):
        pass
