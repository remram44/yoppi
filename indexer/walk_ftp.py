from ftp.models import File

import re

class RemoteFile:
    # drwxr-xr-x 1 ftp ftp  0 Mar 11 13:49 stuff
    # -r--r--r-- 1 ftp ftp 57 Feb 20  2012 smthg.zip
    _line_regex = re.compile(r"^([a-z-]{10})\s+[0-9]+\s+([^\s]+)\s+([^\s]+)\s+([0-9]+)\s+([A-Za-z]+ [0-9]{1,2}\s+[0-9:]+)\s+(.+)$")
    # Groups:
    #   1: permissions
    #   2: user
    #   3: group
    #   4: filesize (bytes)
    #   5: date
    #   6: filename

    def __init__(self, line):
        m = self._line_regex.match(line)
        self.is_directory = m.group(1)[0] == "d"
        self.size = int(m.group(4))
        self.name = m.group(6)

    def __str__(self):
        return self.name

def walk_ftp(server, connection, path='/'):
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

    # TODO : purge deleted files

    for file in files:
        nb_files += 1

        print "%s : %s (%s)" % (path, file.name, (file.is_directory and "d") or "f")

        if file.is_directory:
            n, file.size = walk_ftp(server, connection, path + '/' + file.name)
            nb_files += n

        total_size += file.size

        try:
            ftp_file = File.objects.get(
                    server=server,
                    name=file.name, path=path)
            ftp_file.is_directory = file.is_directory
            ftp_file.size = file.size
            ftp_file.save()
        except File.DoesNotExist:
            ftp_file = File(
                    server=server,
                    name=file.name, path=path,
                    is_directory=file.is_directory,
                    size=file.size)
            ftp_file.save()

    return nb_files, total_size
