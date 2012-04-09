class InvalidAddress(ValueError):
    pass


class IP:
    def __init__(self, i):
        if isinstance(i, IP):
            self.num = i.num
        elif type(i) == str:
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
        elif type(i) == int or type(i) == long:
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


class IPRangeIterator:
    def __init__(self, range):
        self.range = range
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
        return self.first == other.first

    def contains(self, ip):
        if not isinstance(ip, IP):
            ip = IP(ip)
        return self.first < ip < self.last or ip in (self.first, self.last)

    def __iter__(self):
        return IPRangeIterator(self)


class IPSet:
    def __init__(self):
        self.ranges = []

    def add(self, range):
        if not isinstance(range, IPRange):
            range = IPRange(range)
        self.ranges.append(range)
        # TODO : Compact this stuff!

    def contains(self, ip):
        ip = IP(ip)
        for range in self.ranges:
            if range.contains(ip):
                return True

        return False

    def intersection(self, other):
        # TODO
        pass
