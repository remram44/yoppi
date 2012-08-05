import os
os.environ["DJANGO_SETTINGS_MODULE"] = "yoppi.settings"

from yoppi.indexer.app import get_project_indexer
import sys
import logging

logging.basicConfig(level=logging.INFO,
                    format='%(levelname)s:%(name)s:%(asctime)s:%(message)s')
i = get_project_indexer()
i.run(sys.argv)
