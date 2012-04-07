from functools import total_ordering
import bisect


class InvalidAddress(ValueError):
    pass


def IP(i):
    if type(i) == str:
        c = i.split('.')
        if len(c) != 4:
            raise InvalidAddress("Not in IPv4 format")
        try:
            c = [int(v) for v in c]
        except ValueError:
            raise InvalidAddress("Invalid number")
        for v in c:
            if v < 0 or v >= 256:
                raise InvalidAddress("Byte not in [0-255]")
        return ((c[0]*256 + c[1])*256 + c[2])*256 + c[3]
    elif type(i) == int or type(i) == long:
        return i
    else:
        raise TypeError("Expected str or int, got %s" % type(i))


@total_ordering
class IPRange:
    def __init__(self, first, last=None):
        if (not last and (type(first) == list or type(first) == tuple) and
                len(first) == 2):
            first, last = first
        elif not last:
            last = first
        self.first = IP(first)
        self.last = IP(last)

    def __lt__(self, other):
        return self.first < other.first

    def __eq__(self, other):
        return self.first == other.first

    def contains(self, ip):
        if type(ip) != int and type(ip) != long:
            ip = IP(ip)
        return self.first <= ip and ip <= self.last


class IPSet:
    def __init__(self):
        self.ranges = []

    def add(self, range):
        if type(range) != IPRange:
            range = IPRange(range)
        self.ranges.append(range)
        # TODO : Compact this stuff!

    def contains(self, ip):
        ip = IP(ip)
        for range in self.ranges:
            if range.contains(ip):
                return True

        return False
