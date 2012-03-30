from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse
from ftp.models import FtpServer, File


def index(request):
    servers = FtpServer.objects.all()
    return render_to_response(
        'ftp/index.html',
        {'servers': servers, 'active_server': None}
    )


def server(request, address):
    servers = FtpServer.objects.all()
    server = get_object_or_404(FtpServer, address=address)
    files = server.files.all()
    return render_to_response(
        'ftp/server.html',
        {'servers': servers, 'active_server': server, 'files': files}
    )
