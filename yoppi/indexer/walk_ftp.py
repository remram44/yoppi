import logging
import re

from yoppi.ftp.models import File
from django.utils.translation import ugettext


logger = logging.getLogger(__name__)


MAX_DEPTH = 500
MAX_FILES = 1000000

class SuspiciousFtp(Exception):
    pass

class RemoteFile:
    # drwxr-xr-x 1 ftp ftp  0 Mar 11 13:49 stuff
    # -r--r--r-- 1 ftp ftp 57 Feb 20  2012 smthg.zip
    # TODO : make readable (http://docs.python.org/library/re.html#re.VERBOSE)
    # Note : group is optional, because we've found some idiot with a file with not group ?!?
    _line_regex = re.compile(r"^([a-z-]{10})\s+[0-9]+\s+([^\s]+)\s+([^\s]+)?\s+([0-9]+)\s+([A-Za-z]+ +[0-9]{1,2}\s+[0-9:]+)\s(.+)$")
    # Groups:
    #   1: permissions
    #   2: user
    #   3: group
    #   4: filesize (bytes)
    #   5: date
    #   6: filename

    def __init__(self, line, decode=str.decode):
        m = self._line_regex.match(line)
        if not m:
            raise IOError("invalid LIST format : '%s'"%line)
        self.is_directory = m.group(1)[0] == "d"
        self.is_link = m.group(1)[0] == 'l'
        self.raw_size = int(m.group(4))
        self.size = self.raw_size
        self.raw_name = m.group(6)
        self.name = decode(self.raw_name)

    def __eq__(self, other):
        if not isinstance(other, RemoteFile) and not isinstance(other, File):
            return False
        return (self.is_directory == other.is_directory and
                self.size == other.size and
                self.name == other.name)
        # We don't actually need to compare server and path

    def __ne__(self, other):
        return not self.__eq__(other)

    def toFile(self, server, path):
        return File(
                server=server, path=path,
                name=self.name, is_directory=self.is_directory,
                size=self.size)

    def __str__(self):
        return self.name


class FallbackDecoder(object):
    def __init__(self):
        self.encodings = ['utf-8', 'latin9']
        self.next_enc()

    def next_enc(self):
        try:
            self.enc = self.encodings.pop(0)
        except IndexError:
            raise UnicodeDecodeError("Tried all the encodings for this ftp, "
                                     "none fits.")

    def decode(self, str):
        try:
            return str.decode(self.enc)
        except UnicodeDecodeError:
            self.next_enc()
            logging.info('Switched encoding to %s because of file %s', self.enc, repr(str))
            return self.decode(str)


def _yield_files(server, connection, decode, path, depth):
    if depth > MAX_DEPTH:
        raise SuspiciousFtp(ugettext(
            u"%(server)s's directory depth is more than %(max_depth)d. "
            "It doesn't seem legit.") %
            dict(server=server.display_name(), max_depth=MAX_DEPTH))

    files = []
    connection.dir(path, lambda line: files.append(RemoteFile(line, decode)))

    # For ftp, root is '/', but for us, it's ''
    if path == '/':
        path = ''

    for f in files:
        if f.is_link:
            continue
        if f.is_directory:
            for child in _yield_files(server, connection, decode,
                                      '%s/%s' % (path, f.raw_name),
                                      depth + 1):
                f.size += child[1].size
                yield child
        yield decode(path), f


def yield_files(server, connection):
    """Iterates over the ftp and yield all the files as tuples
    (path, RemoteFile)"""
    decode = FallbackDecoder().decode
    return _yield_files(server, connection, decode, '/', 0)


def walk_ftp(server, connection, db_files):
    nb_files = 0
    total_size = 0

    to_insert = []
    to_delete = []

    for path, file in yield_files(server, connection):
        nb_files += 1
        if nb_files > MAX_FILES:
            raise SuspiciousFtp(ugettext(
                    u"%(server)s has more than %(max_files)d files. "
                    "It doesn't seem legit.") %
                    dict(server=server.display_name(), max_files=MAX_FILES))
        total_size += file.raw_size

        try:
            ftp_file = db_files.pop(u'%s/%s' % (path, file.name))
        except KeyError:
            # New file -- we have to insert it
            to_insert.append(file.toFile(server, path))
        else:
            # Existing file -- it is more efficient to delete and recreate it
            # as we can do both operations in bulk mode
            if file != ftp_file:
                to_delete.append(ftp_file.id)
                to_insert.append(file.toFile(server, path))

    return to_insert, to_delete, nb_files, total_size
