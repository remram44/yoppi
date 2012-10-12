from django.test import TestCase, Client
from django.utils import timezone, translation

from yoppi.ftp.models import FtpServer, guess_file_icon


class BasicTest(TestCase):
    fixtures = ['basic.json']

    def setUp(self):
        translation.activate('en-US')

    def test_servers_list(self):
        # Query the index
        response = self.client.get('/')

        # Get the servers passed to the templates
        servers = response.context['servers']

        # Check the values
        self.assertEqual(len(servers), 4)
        names = [s.display_name() for s in servers]
        self.assertEqual(names, [u'192.168.0.12', u"Madjar's bazaar",
                                 u'My paper ftp', u"Remram's room"])

    def test_files_list(self):
        expected_files = [
            ('/server/192.168.0.12', [
                'mirror'
            ]),
            ('/server/192.168.0.12/mirror/empty', []),
            ('/server/192.168.0.12/mirror/debian-amd64', [
                'debian-testing-amd64-CD-1.iso',
                'debian-testing-amd64-CD-2.iso',
                'debian-testing-amd64-CD-3.iso',
                'debian-testing-amd64-CD-4.iso',
                'debian-testing-amd64-CD-5.iso',
            ]),
            ('/server/192.168.0.42', [
                'dir',
                'requirements.txt',
            ]),
        ]

        for uri, exp in expected_files:
            response = self.client.get(uri)
            files = response.context['files']
            names = [e.name for e in files]
            self.assertEqual(names, exp)

    def test_search(self):
        response = self.client.get('/search/?query=paris')
        self.assertEqual(len(response.context['files']), 1)

        response = self.client.get('/search/?query=testing')
        self.assertEqual(len(response.context['files']), 5)

    def test_search_empty(self):
        response = self.client.get('/search/', follow=False)
        self.assertRedirects(response, '/', status_code=302)

    def test_download_dir(self):
        response = self.client.get('/download/192.168.0.12/mirror', follow=False)
        self.assertEqual(response.status_code, 404)

    def test_download(self):
        response = self.client.get('/download/192.168.0.37/todo.txt', follow=False)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], 'ftp://192.168.0.37/todo.txt')

        response = self.client.get('/download/192.168.0.42/dir/icon.png', follow=False)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], 'ftp://192.168.0.42/dir/icon.png')

    def test_time_format(self):
        self.assertEqual(FtpServer._format_duration(5), u"5 seconds")
        self.assertEqual(FtpServer._format_duration(-5), u"just now")
        self.assertEqual(FtpServer._format_duration(0), u"just now")
        self.assertEqual(FtpServer._format_duration(
                2 * 60 + 8),
                u"2 minutes")
        self.assertEqual(FtpServer._format_duration(
                (23 * 60 + 18) * 60 + 54),
                u"23 hours")
        self.assertEqual(FtpServer._format_duration(
                ((4 * 24 + 3) * 60 + 18) * 60 + 54),
                u"4 days")
        self.assertEqual(FtpServer._format_duration(
                ((1024 * 24 + 3) * 60 + 18) * 60 + 54),
                u"146 weeks")


class FileIconsTest(TestCase):
    def test_common_extensions(self):
        self.assertEqual(guess_file_icon('tagada.avi'), 'film')
        self.assertEqual(guess_file_icon('tagada.mkv'), 'film')
        self.assertEqual(guess_file_icon('tagada.mp3'), 'music')

    def test_uppercase(self):
        self.assertEqual(guess_file_icon('tagada.MP3'), 'music')

    def test_application_x(self):
        self.assertEqual(guess_file_icon('tagada.flac'), 'music')