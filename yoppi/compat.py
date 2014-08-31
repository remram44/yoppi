import sys


PY3 = sys.version_info[0] == 3

if PY3:
    unicode_ = str
    basestring_ = str
    baseint_ = int

    izip = zip
    irange = range
    iteritems = dict.items
    itervalues = dict.values
    listvalues = lambda d: list(d.values())
else:
    unicode_ = unicode
    basestring_ = (unicode_, bytes)
    baseint_ = (int, long)

    import itertools
    izip = itertools.izip
    irange = xrange
    iteritems = dict.iteritems
    itervalues = dict.itervalues
    listvalues = dict.values
