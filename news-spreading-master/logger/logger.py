import logging
import os
import sys


def configLogger():
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    file_handler = logging.FileHandler(_get_logfile_name())
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)


def _get_logfile_name():
    executable_name = os.path.basename(sys.argv[0]).split('.')[0]
    return '/tmp/logs/%s.log' % executable_name
