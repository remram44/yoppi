from django.db import models
import math
from datetime import datetime


class FtpServer(models.Model):
    address = models.CharField(
            "server's DNS name or IP address",
            primary_key=True, max_length=200)
    name = models.CharField(
            "optionnal readable name", max_length=30, blank=True, default='')
    online = models.BooleanField(default=True)
    size = models.IntegerField(default=0)
    last_online = models.DateTimeField(default=lambda: datetime.now())
    # Either NULL (not indexing) or the time when the indexing process began
    # This field has no impact on the users but is used to prevent two
    # concurrent processes from indexing the same server
    indexing = models.DateTimeField(
            "indexing start date or null", null=True, default=None)

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
        return ('ftp.views.server', (self.address, ''))

    def display_lastonline(self):
        t = (datetime.now() - self.last_online).total_seconds()
        last_label = ''
        for length, label in FtpServer._times:
            if t > length:
                t /= length
                last_label = label
            else:
                break
        return "%d %s" % (int(t), last_label)


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
            return ('ftp.views.server', (self.server.address, self.fullpath()))
        else:
            return ('ftp.views.download', (self.server.address, self.fullpath()))

    def fullpath(self):
        return self.path + u"/" + self.name
