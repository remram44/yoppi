# -*- coding: utf-8 -*-
import warnings
from django.test import TestCase
from django.utils import unittest
import mock
from iptools import IP, IPRange, IPSet, InvalidAddress, parse_ip_ranges


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

    def test_set_compact(self):
        set = IPSet()
        set.add(['160.228.152.1', '160.228.154.4'])
        self.assertEqual(set.ranges, [
            IPRange('160.228.152.1', '160.228.154.4'),
        ])
        set.add(['192.168.0.2', '192.168.2.200'])
        self.assertEqual(set.ranges, [
            IPRange('160.228.152.1', '160.228.154.4'),
            IPRange('192.168.0.2', '192.168.2.200'),
        ])
        set.add(['160.228.153.255', '170.2.3.4'])
        self.assertEqual(set.ranges, [
            IPRange('160.228.152.1', '170.2.3.4'),
            IPRange('192.168.0.2', '192.168.2.200'),
        ])
        set.add(['170.2.3.5', '193.2.3.4'])
        self.assertEqual(set.ranges, [
            IPRange('160.228.152.1', '193.2.3.4'),
        ])

    def test_set_iter(self):
        set = IPSet()
        set.add(['10.8.1.5', '10.8.1.7'])
        set.add(['10.9.2.2', '10.9.2.4'])
        set.add(['10.9.2.3', '10.9.2.5'])
        iter = set.__iter__()
        self.assertEqual(iter.next(), IP('10.8.1.5'))
        self.assertEqual(iter.next(), IP('10.8.1.6'))
        self.assertEqual(iter.next(), IP('10.8.1.7'))
        self.assertEqual(iter.next(), IP('10.9.2.2'))
        self.assertEqual(iter.next(), IP('10.9.2.3'))
        self.assertEqual(iter.next(), IP('10.9.2.4'))
        self.assertEqual(iter.next(), IP('10.9.2.5'))
        self.assertRaises(StopIteration, iter.next)

    def test_ip_range_parser(self):
        expected = [
            IPRange('10.8.1.1'),
        ]
        self.assertEqual(parse_ip_ranges(IP('10.8.1.1')).ranges, expected)
        self.assertEqual(parse_ip_ranges('10.8.1.1').ranges, expected)
        self.assertEqual(parse_ip_ranges(168296705).ranges, expected)
        self.assertEqual(parse_ip_ranges(['10.8.1.1']).ranges, expected)
        self.assertEqual(parse_ip_ranges(
                [('10.8.1.1', '10.8.1.1')]).ranges,
                expected)
        expected = [
            IPRange('10.0.0.1', '10.1.2.3')
        ]
        # Special case -- will print a warning
        with warnings.catch_warnings(record=True) as w:
            self.assertEqual(
                    parse_ip_ranges(('10.0.0.1', '10.1.2.3')).ranges,
                    expected)
            self.assertEqual(len(w), 1)
            self.assertIn('Warning: parse_ip_range(): got a two addresses, '
                          'assuming a range rather than two distinct addresses'
                          , str(w[0].message))
        self.assertEqual(
                parse_ip_ranges([('10.0.0.1', '10.1.2.3')]).ranges,
                expected)
        expected = [
            IPRange('10.0.0.1', '10.0.0.1'),
            IPRange('10.2.3.4', '10.2.9.9'),
        ]
        self.assertEqual(
                parse_ip_ranges(['10.0.0.1', ('10.2.3.4', '10.2.9.9')]).ranges,
                expected)
        expected = [
            IPRange('10.0.0.1', '10.0.0.2'),
            IPRange('10.2.3.4', '10.2.9.9'),
        ]
        self.assertEqual(
                parse_ip_ranges(
                        ['10.0.0.1', ('10.2.3.4', '10.2.9.9'), '10.0.0.2']
                ).ranges,
                expected)
        self.assertEqual(
                parse_ip_ranges([
                        IP('10.0.0.1'), IP('10.0.0.2'),
                        IPRange('10.2.3.4', IP('10.2.9.9'))
                ]).ranges,
                expected)


class IndexerTestCase(TestCase):
    def setUp(self):
        self.patcher = mock.patch('ftplib.FTP')
        self.FTP = self.patcher.start()

        def fake_dir(path, callback):
            if path == '/':
                callback('-r--r--r-- 1 ftp ftp 57 Feb 20  2012  smthg.zip')
                callback('drwxr-xr-x 1 ftp ftp  0 Mar 11 13:49 stuff')
            elif path == '/stuff':
                callback('-r--r--r-- 1 ftp ftp 1000 Feb 20  2012 mysterioüs.zip')

        self.FTP().dir = fake_dir

    def tearDown(self):
        self.patcher.stop()

    def _get_indexer(self):
        from yoppi.indexer.app import Indexer
        return Indexer()

    def test_basic_index(self):
        indexer = self._get_indexer()
        indexer.index('10.9.8.7')

        from yoppi.ftp.models import FtpServer
        ftp = FtpServer.objects.get()
        self.assertEqual(ftp.address, '10.9.8.7')
        self.assertEqual(ftp.size, 1057)

        files = ftp.files.all()
        self.assertEqual(len(files), 3)

    def test_indexing_twice_doesnt_change_the_db(self):
        indexer = self._get_indexer()
        indexer.index('10.9.8.7')
        from yoppi.ftp.models import File
        ids = list(File.objects.values_list('id'))

        indexer.index('10.9.8.7')
        new_ids = list(File.objects.values_list('id'))

        self.assertEqual(ids, new_ids)

    def test_leading_whitespace(self):
        indexer = self._get_indexer()
        indexer.index('10.9.8.7')

        from yoppi.ftp.models import File
        self.assertEqual(File.objects.filter(name=u' smthg.zip').count(),
                1)

    def test_infinite_loop(self):
        def fake_dir(path, callback):
            callback('drwxr-xr-x 1 ftp ftp  0 Mar 11 13:49 stuff')

        self.FTP().dir = fake_dir

        indexer = self._get_indexer()

        from yoppi.indexer.walk_ftp import SuspiciousFtp
        with self.assertRaises(SuspiciousFtp):
            indexer.index('10.9.8.7')

    def test_lot_of_files(self):
        patcher = mock.patch('yoppi.indexer.walk_ftp.MAX_FILES', 10)
        patcher.start()

        def fake_dir(path, callback):
            for i in xrange(11):
                callback('-r--r--r-- 1 ftp ftp 57 Feb 20  2012 smthg.zip')

        self.FTP().dir = fake_dir

        indexer = self._get_indexer()

        from yoppi.indexer.walk_ftp import SuspiciousFtp
        with self.assertRaises(SuspiciousFtp):
            indexer.index('10.9.8.7')

        patcher.stop()


if __name__ == '__main__':
    unittest.main()
