from django.shortcuts import render_to_response, get_object_or_404, redirect
from ftp.models import FtpServer, File

def all_servers():
    return list(FtpServer.objects.order_by('-online', '-size'))

def index(request):
    return render_to_response(
        'ftp/index.html',
        {'servers': all_servers()}
    )


def server(request, address, path=''):
    if path != '' and path[-1] == '/':
        path = path[:-1]
    server = get_object_or_404(FtpServer, address=address)
    files = server.files.filter(path=path).order_by('name')
    return render_to_response(
        'ftp/server.html',
        {'servers': all_servers(), 'active_server': server, 'files': list(files), 'path': path}
    )


def search(request):
    try:
        query = request.GET['query']
        # TODO : A simple contains is probably not enough
        files = File.objects.filter(name__contains=query).order_by('name')
        return render_to_response(
            'ftp/search.html',
            {'servers': all_servers(), 'files': list(files), 'query': query}
        )
    except KeyError:
        return redirect('ftp.views.index')
