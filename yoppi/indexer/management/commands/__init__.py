import logging
from django.utils.functional import lazy
from django.utils.translation import pgettext


LEVELS = {
    0: logging.ERROR,
    1: logging.WARNING,
    2: logging.INFO,
    3: logging.DEBUG
}

def setup_logging(verbosity):
    logging.basicConfig(level=LEVELS[int(verbosity)],
                        format='%(message)s')

# Some kludge to fix #20
fixed_pgettext_lazy = lazy(pgettext, str)
