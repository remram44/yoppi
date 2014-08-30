import itertools
from bisect import bisect
import warnings

from django.utils.translation import ugettext

class InvalidAddress(ValueError):
    pass


class IP:
    def __init__(self, i):
        if isinstance(i, IP):
            self.num = i.num
        elif isinstance(i, basestring):
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
            self.num = ((c[0]*256 + c[1])*256 + c[2])*256 + c[3]
        elif isinstance(i, (int, long)):
            self.num = i
        else:
            raise TypeError("Expected str or int, got %s" % type(i))

    def __lt__(self, other):
        return self.num < other.num

    def __eq__(self, other):
        return self.num == other.num

    def __str__(self):
        return "%d.%d.%d.%d" % (
            (self.num >> 24) & 0xFF,
            (self.num >> 16) & 0xFF,
            (self.num >>  8) & 0xFF,
            (self.num      ) & 0xFF)

    def __int__(self):
        return self.num

    def __repr__(self):
        return "IP(%s)" % self.__str__()


class IPRangeIterator:
    def __init__(self, range, pos=None):
        self.range = range
        if pos is not None:
            self.pos = pos
        else:
            self.pos = range.first.num

    def __iter__(self):
        return self

    def next(self):
        if self.pos > self.range.last.num:
            raise StopIteration
        else:
            self.pos += 1
            return IP(self.pos-1)


class IPRange:
    def __init__(self, first, last=None):
        if (not last and (type(first) == list or type(first) == tuple) and
                len(first) == 2):
            first, last = first
        elif not last:
            last = first

        self.first = first
        if not isinstance(self.first, IP):
            self.first = IP(self.first)
        self.last = last
        if not isinstance(self.last, IP):
            self.last = IP(self.last)

    def __lt__(self, other):
        return self.first < other.first

    def __eq__(self, other):
        return (self.first, self.last) == (other.first, other.last)

    def __len__(self):
        return self.last.num - self.first.num + 1

    def contains(self, ip):
        if not isinstance(ip, IP):
            ip = IP(ip)
        return self.first < ip < self.last or ip in (self.first, self.last)

    def iter_from(self, ip):
        if not isinstance(ip, IP):
            ip = IP(ip)
        if ip.num < self.first.num:
            return IPRangeIterator(self, self.first.num)
        else:
            return IPRangeIterator(self, ip.num)

    def __iter__(self):
        return IPRangeIterator(self)

    def __repr__(self):
        return "IPRange(%s, %s)" % (str(self.first), str(self.last))


class IPSet:
    def __init__(self):
        self.ranges = []
        self._length = None

    def add(self, range):
        if not isinstance(range, IPRange):
            range = IPRange(range)

        # Find insertion pos
        pos = bisect(self.ranges, range)

        # We might overlap with the range immediately left, plus any number of
        # ranges right

        # Merge left
        if pos > 0 and range.first.num <= self.ranges[pos-1].last.num+1:
            self.ranges[pos-1].last = range.last
            pos -= 1
            range = self.ranges[pos]
        else:
            self.ranges.insert(pos, range)

        # Merge right
        while (pos+1 < len(self.ranges) and
                self.ranges[pos+1].first.num+1 <= range.last.num):
            range.last = IP(
                    max(range.last.num, self.ranges[pos+1].last.num))
            del self.ranges[pos+1]

        self._length = None

    def contains(self, ip):
        ip = IP(ip)
        pos = bisect(self.ranges, IPRange(ip)) - 1
        if pos >= 0:
            return self.ranges[pos].contains(ip)

    def __len__(self):
        if self._length is None:
            self._length = sum(len(r) for r in self.ranges)
        return self._length

    def __iter__(self):
        return itertools.chain.from_iterable(self.ranges)

    def loop_iter_from(self, ip):
        if not isinstance(ip, IP):
            ip = IP(ip)
        if not self.ranges:
            # Only case where the iterator won't be infinite
            return iter([])
        pos = bisect(self.ranges, IPRange(ip)) - 1
        if pos >= 0:
            return itertools.chain(
                    # Partial iteration through the first range
                    self.ranges[pos].iter_from(ip),
                    # Iteration through the following ranges
                    itertools.chain.from_iterable(self.ranges[pos+1:]),
                    # Continue iterating
                    itertools.chain.from_iterable(
                            itertools.cycle(self.ranges)))
        else:
            return itertools.chain.from_iterable(itertools.cycle(self.ranges))
        # Documentation states that the iterable passed to chain.from_iterable
        # "is evaluated lazily", so we assume that it is legal to pass it an
        # infinite iterator

    def first(self):
        if self.ranges:
            return self.ranges[0].first
        else:
            return None


def parse_ip_ranges(ranges):
    if isinstance(ranges, IPSet):
        return ranges

    ipset = IPSet()

    if isinstance(ranges, (IPRange, IP, str, long, int)):
        ipset.add(ranges)
        return ipset

    # Special case: ranges = (first, last)
    # We assume that this is a single range and not two ranges of one address
    # each
    if (len(ranges) == 2 and
            all(isinstance(r, (IP, str, long, int)) for r in ranges)):
        range = IPRange(ranges[0], ranges[1])
        warnings.warn(ugettext(
                u"Warning: parse_ip_range(): got two addresses, "
                "assuming a range rather than two distinct addresses\n"
                "Wrap them inside a tuple to remove this warning, eg:\n"
                "  'IP_RANGES': (\n"
                "      ('{0!s}', '{1!s}'),\n"
                "  ),\n"
                "instead of:\n"
                "  'IP_RANGES': (\n"
                "      '{0!s}', '{1!s}'\n"
                "  ),\n").format(range.first, range.last))
        ipset.add(range)
        return ipset

    for r in ranges:
        # List and tuples (first, last)
        if isinstance(r, (list, tuple)):
            if len(r) == 2:
                ipset.add(IPRange(r[0], r[1]))
            else:
                raise ValueError("two addresses needed to define a range!")
        # Works for IP, IPRange, str, long, int
        else:
            ipset.add(r)
    return ipset
