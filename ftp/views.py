from django.shortcuts import render_to_response, get_object_or_404, redirect
from ftp.models import FtpServer, File


def index(request):
    servers = FtpServer.objects.order_by('-online', '-size')
    return render_to_response(
        'ftp/index.html',
        {'servers': list(servers), 'active_server': None}
    )


def server(request, address):
    servers = FtpServer.objects.all()
    server = get_object_or_404(FtpServer, address=address)
    files = server.files.order_by('name')
    return render_to_response(
        'ftp/server.html',
        {'servers': list(servers), 'active_server': server, 'files': list(files)}
    )


def search(request):
    try:
        query = request.GET['query']
        # TODO : A simple contains is probably not enough
        files = File.objects.filter(name__contains=query)
        return render_to_response(
            'ftp/search.html',
            {'files': list(files), 'query': query}
        )
    except KeyError:
        return redirect('ftp.views.index')
