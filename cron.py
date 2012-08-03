import os
os.environ["DJANGO_SETTINGS_MODULE"] = "yoppi.settings"

from yoppi.indexer.app import get_project_indexer
import sys

i = get_project_indexer()
i.run(sys.argv)
