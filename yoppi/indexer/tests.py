from django.test import TestCase
from django.utils import unittest
import mock
from iptools import IP, IPRange, IPSet, InvalidAddress


class TestIPTools(unittest.TestCase):
    def test_ip(self):
        self.assertEqual(IP('0.0.0.0').num, 0)
        self.assertEqual(IP('1.2.3.4').num, 16909060)
        self.assertRaises(InvalidAddress, lambda: IP('1.2.3'))
        self.assertRaises(InvalidAddress, lambda: IP('1.256.3.4'))
        self.assertRaises(InvalidAddress, lambda: IP('1.-2.3.4'))
        self.assertRaises(InvalidAddress, lambda: IP('1.2.3,0.4'))

    def test_range_init(self):
        range = IPRange('192.168.0.1')
        self.assertEqual(range, IPRange('192.168.0.1', '192.168.0.1'))
        self.assertEqual(range, IPRange(['192.168.0.1', '192.168.0.1']))

    def test_range(self):
        range = IPRange('10.8.0.1', '10.8.2.255')
        self.assertFalse(range.contains('10.7.255.4'))
        self.assertFalse(range.contains('10.8.3.0'))
        self.assertTrue(range.contains('10.8.2.1'))
        self.assertTrue(range.contains('10.8.1.1'))

    def test_range_iter(self):
        range = IPRange('10.8.255.254', '10.9.0.2')
        iter = range.__iter__()
        self.assertEqual(iter.next(), IP('10.8.255.254'))
        self.assertEqual(iter.next(), IP('10.8.255.255'))
        self.assertEqual(iter.next(), IP('10.9.0.0'))
        self.assertEqual(iter.next(), IP('10.9.0.1'))
        self.assertEqual(iter.next(), IP('10.9.0.2'))
        self.assertRaises(StopIteration, iter.next)

    def test_ipset(self):
        set = IPSet()
        self.assertRaises(InvalidAddress, lambda: set.contains('160.228.153.256'))

    def test_simpleset(self):
        set = IPSet()
        self.assertEqual(len(set.ranges), 0)
        self.assertFalse(set.contains('192.168.0.3'))

    def test_set_basic(self):
        set = IPSet()

        set.add(['160.228.152.1', '160.228.154.4'])
        self.assertEqual(len(set.ranges), 1)

        self.assertTrue(set.contains('160.228.153.252'))
        self.assertFalse(set.contains('1.2.3.4'))
        self.assertFalse(set.contains('160.228.152.0'))
        self.assertFalse(set.contains('160.228.154.5'))

        self.assertFalse(set.contains('192.168.1.24'))

        set.add(['192.168.0.2', '192.168.2.200'])

        self.assertTrue(set.contains('192.168.1.24'))

    @unittest.expectedFailure  # Not implemented yet
    def test_set_compact(self):
        set = IPSet()
        set.add(['160.228.152.1', '160.228.154.4'])
        self.assertEqual(len(set.ranges), 1)
        set.add(['192.168.0.2', '192.168.2.200'])
        self.assertEqual(len(set.ranges), 2)
        set.add(['160.228.154.255', '170.2.3.4'])
        self.assertEqual(len(set.ranges), 2)
        set.add(['170.2.3.5', '193.2.3.4'])
        self.assertEqual(len(set.ranges), 1)


class IndexerTestCase(TestCase):
    def setUp(self):
        self.patcher = mock.patch('ftplib.FTP')
        self.FTP = self.patcher.start()

        def fake_dir(path, callback):
            if path == '/':
                callback('-r--r--r-- 1 ftp ftp 57 Feb 20  2012 smthg.zip')
                callback('drwxr-xr-x 1 ftp ftp  0 Mar 11 13:49 stuff')
            elif path == '/stuff':
                callback('-r--r--r-- 1 ftp ftp 1000 Feb 20  2012 mysterious.zip')

        self.FTP().dir = fake_dir


    def tearDown(self):
        self.patcher.stop()

    def test_basic_index(self):
        from yoppi.indexer.app import Indexer
        indexer = Indexer()
        indexer.index('10.9.8.7')

        from yoppi.ftp.models import FtpServer, File
        ftp = FtpServer.objects.get()
        self.assertEqual(ftp.address, '10.9.8.7')
        self.assertEqual(ftp.size, 1057)

        files = ftp.files.all()
        self.assertEqual(len(files), 3)


if __name__ == '__main__':
    unittest.main()
