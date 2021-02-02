import logging
import os
import sys
import time

import yaml

from core.connect_db import connect_db

SETTINGS_FILE = 'config.yaml'


def load_settings():
    with open(SETTINGS_FILE, 'r') as settings_file:
        try:
            return yaml.load(settings_file)
        except yaml.YAMLError as e:
            logging.log(logging.DEBUG, 'Error reading the settings file: {"error": %s}' % e)
            sys.exit(1)


def load_environment():
    os.environ['TZ'] = 'UTC'
    time.tzset()

    # connect to db
    settings = load_settings()
    mongo_config = settings['dbs']['mongo']
    connect_db(**mongo_config)
