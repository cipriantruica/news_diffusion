import logging
import sys

from mongoengine import connect
from pymongo.errors import ServerSelectionTimeoutError

logger = logging.getLogger()

database_connection = None


def connect_db(host, port, db):
    global database_connection
    if not database_connection:
        url = 'mongodb://%s:%d/%s' % (host, port, db)
        logger.info('Connecting to %s' % url)
        try:
            database_connection = connect(host=url)
            database_connection.server_info()
            logger.info('Connection successful to %s' % url)
        except ServerSelectionTimeoutError as connection_error:
            logger.error('Connecting to %s failed: %s' % (url, connection_error))
            sys.exit(1)
    return database_connection
