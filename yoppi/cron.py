import os
os.environ["DJANGO_SETTINGS_MODULE"] = "settings"

from django.conf import settings as django_settings


try:
    settings = django_settings.INDEXER_SETTINGS
except KeyError:
    settings = {}


from yoppi.indexer.app import Indexer
import sys

i = Indexer(**settings)
i.run(sys.argv)
