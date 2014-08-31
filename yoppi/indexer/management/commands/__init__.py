import logging


LEVELS = {
    0: logging.ERROR,
    1: logging.WARNING,
    2: logging.INFO,
    3: logging.DEBUG
}

def setup_logging(verbosity):
    logging.basicConfig(level=LEVELS[int(verbosity)],
                        format='%(message)s')
