from django.contrib import admin

from yoppi.ftp.models import FtpServer, File


admin.site.register(FtpServer)
admin.site.register(File)
