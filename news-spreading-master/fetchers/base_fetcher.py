import logging

from core.connect_db import connect_db
from logger.logger import configLogger
from settings.settings import load_settings

logger = logging.getLogger()


class BaseFetcher(object):

    def __init__(self):
        super(BaseFetcher, self).__init__()

        configLogger()
        self._connect_to_db()

    def run(self):
        running = True
        while running:
            try:
                self._run()
            except Exception as e:
                logger.error('Got error while running : %r' % e)
                running = False
                raise

    def _run(self):
        pass

    def _connect_to_db(self):
        settings = load_settings()
        mongo_config = settings['dbs']['mongo']
        con = connect_db(**mongo_config)
