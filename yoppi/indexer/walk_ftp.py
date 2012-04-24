import re

from yoppi.ftp.models import File

MAX_DEPTH = 1000
MAX_FILES = 1000000

class SuspiciousFtp(Exception):
    pass

class RemoteFile:
    # drwxr-xr-x 1 ftp ftp  0 Mar 11 13:49 stuff
    # -r--r--r-- 1 ftp ftp 57 Feb 20  2012 smthg.zip
    _line_regex = re.compile(r"^([a-z-]{10})\s+[0-9]+\s+([^\s]+)\s+([^\s]+)\s+([0-9]+)\s+([A-Za-z]+ +[0-9]{1,2}\s+[0-9:]+)\s(.+)$")
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
            raise IOError("invalid LIST format\n")
        self.is_directory = m.group(1)[0] == "d"
        self.is_link = m.group(1)[0] == 'l'
        self.size = int(m.group(4))
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
                name=self.name, is_directory=self.is_directory, size=self.size)

    def __str__(self):
        return self.name


class FallbackDecoder(object):
    def __init__(self):
        self.encodings = ['utf-8', 'latin9']
        self.next_enc()

    def next_enc(self):
        try:
            self.enc = self.encodings.pop()
        except IndexError:
            raise UnicodeDecodeError('Tried all the encodings for this ftp,'
                                     ' none fits.')

    def decode(self, str):
        try:
            return str.decode(self.enc)
        except UnicodeDecodeError:
            self.next_enc()
            return self.decode(str)


def yield_files(server, ftp):
    """Iterates over the ftp and yield all the files as tuples
    (path, RemoteFile)"""
    stack = [('/', 0)]
    files = []
    decode = FallbackDecoder().decode

    def callback(line):
        files.append(RemoteFile(line, decode))

    while stack:
        path, depth = stack.pop()
        if depth > MAX_DEPTH:
            raise SuspiciousFtp("%s directory depth is more than %s."
                                " It doesn't seem legit"%
                                (MAX_DEPTH, server.display_name()))
        ftp.dir(path, callback)

        # For ftp, root is '/', but for us, it's ''
        if path == '/':
            path = ''

        for f in files:
            if f.is_link:
                continue
            if f.is_directory:
                stack.append(('%s/%s'%(path, f.raw_name), depth + 1))
            yield decode(path), f

        files = []


def walk_ftp(server, connection, db_files):
    nb_files = 0
    total_size = 0

    to_insert = []
    to_delete = []

    for path, file in yield_files(server, connection):
        nb_files += 1
        if nb_files > MAX_FILES:
            raise SuspiciousFtp("%s has more than %s file."
                                " It doesn't seem legit"%
                                (MAX_FILES, server.display_name()))
        total_size += file.size

        try:
            ftp_file = db_files.pop(u'%s/%s'%(path, file.name))
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
