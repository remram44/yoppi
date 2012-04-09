from django.db import models
import math
from django.utils import timezone


class FtpServer(models.Model):
    address = models.CharField(
            "server's DNS name or IP address",
            primary_key=True, max_length=200)
    name = models.CharField(
            "optionnal readable name", max_length=30, blank=True, default='')
    online = models.BooleanField(default=True)
    size = models.IntegerField(default=0)
    last_online = models.DateTimeField(default=lambda: timezone.now())
    # Either NULL (not indexing) or the time when the indexing process began
    # This field has no impact on the users but is used to prevent two
    # concurrent processes from indexing the same server
    indexing = models.DateTimeField(
            "indexing start date or null", null=True, default=None, blank=True)

    # TODO : Locale-dependent
    _times = (
        (1, 'secondes'),
        (60, 'minutes'),
        (60, 'hours'),
        (24, 'days'),
        (7, 'weeks'),
    )

    def display_name(self):
        if self.name != "":
            return self.name
        else:
            return self.address

    def __unicode__(self):
        return self.address

    @models.permalink
    def get_absolute_url(self):
        return ('yoppi.ftp.views.server', (self.address, ''))

    def _seconds_since_lastonline(self):
        td = timezone.now() - self.last_online
        return td.seconds + td.days * 24 * 3600

    def display_lastonline(self):
        t = self._seconds_since_lastonline()
        last_label = ''
        for length, label in FtpServer._times:
            if t > length:
                t /= length
                last_label = label
            else:
                break
        return "%d %s" % (int(t), last_label)


ICONS = {
    'avi': 'film',
    'mkv': 'film',
    'mp3': 'music',
    'ogg': 'music',
}


class File(models.Model):
    server = models.ForeignKey(FtpServer, related_name='files')
    name = models.CharField(max_length=200)
    path = models.CharField(max_length=300, blank=True) # Never ends with '/'
    is_directory = models.BooleanField()
    size = models.IntegerField()

    def __unicode__(self):
        return u"%s:%s/%s" % (unicode(self.server), self.path, self.name)

    @models.permalink
    def get_absolute_url(self):
        if self.is_directory:
            return ('yoppi.ftp.views.server', (self.server.address, self.fullpath()))
        else:
            return ('yoppi.ftp.views.download', (self.server.address, self.fullpath()))

    def fullpath(self):
        return self.path + u"/" + self.name

    def icon(self):
        if self.is_directory:
            return 'folder-open'
        else:
            ext = self.name.rsplit('.', 1)[-1]
            return ICONS.get(ext, 'file')