import unittest

from settings.settings import load_settings
from core.connect_db import connect_db

class BaseBackendTest(unittest.TestCase):

    def setUp(self):
        self.db_clients = []
        configs = load_settings()
        for db_name in configs['dbs'].keys():
            db_configs = configs['dbs'][db_name]
            test_db_name = 'test_%s' % db_configs['db']
            self.db_clients.append(connect_db(db_configs['host'], db_configs['port'], test_db_name))

    def tearDown(self):
        for db_client in self.db_clients:
            db = db_client.get_default_database()
            for collection in db.collection_names():
                if collection != 'system.indexes':
                    db[collection].drop()
            db_client.close()
