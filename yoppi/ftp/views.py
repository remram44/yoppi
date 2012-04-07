from django.shortcuts import render, get_object_or_404, redirect
from django.core.urlresolvers import reverse
from yoppi.ftp.models import FtpServer, File


def all_servers():
    return list(FtpServer.objects.order_by('-online', '-size'))


def decompose_path(server, path):
    hierarchy = [{'name': server, 'url': reverse('yoppi.ftp.views.server', args=[server, ''])}]
    if path != '':
        i = 0
        j = path.find('/', 1)
        while j != -1:
            hierarchy += [{'name': path[(i+1):j], 'url': reverse('yoppi.ftp.views.server', args=[server, path[:j]])}]
            i = j
            j = path.find('/', j+1)

        hierarchy += [{'name': path[(i+1):], 'url': reverse('yoppi.ftp.views.server', args=[server, path]), 'current': True}]
    else:
        hierarchy[0]['current'] = True

    return hierarchy


def index(request):
    return render(
        request,
        'ftp/index.html',
        {'servers': all_servers()}
    )


def server(request, address, path=''):
    if path != '' and path[-1] == '/':
        path = path[:-1]
    server = get_object_or_404(FtpServer, address=address)

    hierarchy = decompose_path(server.address, path)

    files = server.files.filter(path=path).order_by('name')

    return render(
        request,
        'ftp/server.html',
        {'servers': all_servers(), 'active_server': server, 'files': list(files), 'path': path, 'hierarchy': hierarchy}
    )


def search(request):
    try:
        query = request.GET['query']
        # TODO : A simple contains is probably not enough
        files = File.objects.filter(name__contains=query).order_by('name')
        return render(
            request,
            'ftp/search.html',
            {'servers': all_servers(), 'files': list(files), 'query': query}
        )
    except KeyError:
        return redirect('yoppi.ftp.views.index')
