from yoppi.ftp.models import File

import re

class RemoteFile:
    # drwxr-xr-x 1 ftp ftp  0 Mar 11 13:49 stuff
    # -r--r--r-- 1 ftp ftp 57 Feb 20  2012 smthg.zip
    _line_regex = re.compile(r"^([a-z-]{10})\s+[0-9]+\s+([^\s]+)\s+([^\s]+)\s+([0-9]+)\s+([A-Za-z]+ +[0-9]{1,2}\s+[0-9:]+)\s+(.+)$")
    # Groups:
    #   1: permissions
    #   2: user
    #   3: group
    #   4: filesize (bytes)
    #   5: date
    #   6: filename

    def __init__(self, line):
        m = self._line_regex.match(line)
        if m == None:
            raise IOError("invalid LIST format\n")
        self.is_directory = m.group(1)[0] == "d"
        self.size = int(m.group(4))
        self.name = m.group(6)

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

def walk_ftp(server, connection, db_files, path='/'):
    if path == '/':
        path = ''

    files = []

    def callback(line):
        files.append(RemoteFile(line))

    if path == '':
        connection.dir('/', callback)
    else:
        connection.dir(path, callback)

    nb_files = 0
    total_size = 0

    to_insert = []
    to_delete = []

    for file in files:
        nb_files += 1

        # Recursively walk over subdirectories
        if file.is_directory:
            r_to_insert, r_to_delete, r_nb_files, file.size = \
                    walk_ftp(server, connection, db_files, path + '/' + file.name)
            to_insert += r_to_insert
            to_delete += r_to_delete
            nb_files += r_nb_files

        total_size += file.size

        try:
            ftp_file = db_files.pop(path + '/' + file.name)
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
