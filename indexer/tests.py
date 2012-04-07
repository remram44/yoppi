import unittest
from iptools import IP, IPSet, InvalidAddress


class TestIPTools(unittest.TestCase):
    def test_ip(self):
        self.assertEqual(IP('0.0.0.0'), 0)
        self.assertEqual(IP('1.2.3.4'), 16909060)
        self.assertRaises(InvalidAddress, lambda: IP('1.2.3'))
        self.assertRaises(InvalidAddress, lambda: IP('1.256.3.4'))
        self.assertRaises(InvalidAddress, lambda: IP('1.-2.3.4'))
        self.assertRaises(InvalidAddress, lambda: IP('1.2.3,0.4'))

    # TODO : IPRange tests

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
        self.assertEqual(len(set.ranges), 1)
        set.add(['192.168.0.2', '192.168.2.200'])
        self.assertEqual(len(set.ranges), 2)
        set.add(['160.228.154.255', '170.2.3.4'])
        self.assertEqual(len(set.ranges), 2)
        set.add(['170.2.3.5', '193.2.3.4'])
        self.assertEqual(len(set.ranges), 1)


if __name__ == '__main__':
    unittest.main()
