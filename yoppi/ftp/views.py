from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.shortcuts import render, get_object_or_404, redirect
from django.core.urlresolvers import reverse
from django.http import HttpResponse, Http404
from django.utils.encoding import smart_str
from yoppi.ftp.models import FtpServer, File


def all_servers():
    return list(FtpServer.objects.order_by('-online', '-size'))


def decompose_path(server, path):
    address = server.address
    hierarchy = [{'name': server.display_name(), 'url': reverse('yoppi.ftp.views.server', args=[address, ''])}]
    if path != '':
        i = 0
        j = path.find('/', 1)
        while j != -1:
            hierarchy += [{'name': path[(i+1):j], 'url': reverse('yoppi.ftp.views.server', args=[address, path[:j]])}]
            i = j
            j = path.find('/', j+1)

        hierarchy += [{'name': path[(i+1):], 'url': reverse('yoppi.ftp.views.server', args=[address, path]), 'current': True}]
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

    hierarchy = decompose_path(server, path)

    files = (server.files.filter(path=path)
             .order_by('-is_directory', 'name').select_related('server'))

    return render(
        request,
        'ftp/server.html',
        {'servers': all_servers(), 'active_server': server, 'files': list(files), 'path': path, 'hierarchy': hierarchy}
    )


def download(request, address, path):
    server = get_object_or_404(FtpServer, address=address)

    sep = path.rfind('/')
    if sep == -1:
        raise Http404
    filename = path
    path, name = filename[:sep], filename[sep+1:]
    file = get_object_or_404(File, server=server, path=path, name=name, is_directory=False)

    # TODO : download statistics?

    response = HttpResponse(status=302)
    response['Cache-control'] = 'no-cache'
    response['Location'] = smart_str('ftp://%s%s' % (server.address, filename))
    return response


def search(request):
    query = request.GET.get('query')
    if not query:
        # not query or empty query
        return redirect('yoppi.ftp.views.index')

    # TODO : A simple contains is probably not enough
    all_files = (File.objects.filter(name__icontains=query)
                 .order_by('-server__online','-is_directory', 'name').select_related('server'))
    paginator = Paginator(all_files, 100)
    page = request.GET.get('page')
    try:
        files = paginator.page(page)
    except PageNotAnInteger:
        files = paginator.page(1)
    except EmptyPage:
        files = paginator.page(paginator.num_pages)

    return render(
        request,
        'ftp/search.html',
        {'servers': all_servers(), 'files': files, 'query': query}
    )


def error_404(request):
    return render(
        request,
        '404.html',
        status=404)


def error_500(request):
    return render(
        request,
        '500.html',
        status=500)
