import os.path
import sys
import sqlite3
import logging

import abbr
import iana
import geonames
import topcities

FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(level=logging.INFO, format=FORMAT)
log = logging.getLogger()

seperator = "================================="

data_path = './data/'
log_dir = './log/'

db_file = data_path + 'timegeopack.sqlite3'


def db():
    return sqlite3.connect(db_file)


def setup_logging():
    os.makedirs(log_dir, exist_ok=True)

    formatter = logging.Formatter(
        '[%(asctime)s] %(name)-10s%(levelname)-6s %(message)s', '%Y-%m-%d %H:%M:%S')
    global log
    for h in log.handlers:
        log.removeHandler(h)

    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(formatter)
    fch = logging.FileHandler(log_dir + 'timegeopack.log', 'w')
    fch.setFormatter(formatter)

    log.setLevel(logging.INFO)
    log.addHandler(ch)
    log.addHandler(fch)


def setup_db():
    if os.path.exists(db_file):
        try:
            os.unlink(db_file)
        except FileNotFoundError as e:
            log.error('Unable to Delete database to start from scratch.')

    try:
        abbr.createTable()
        iana.createTable()
        geonames.createTables()
        topcities.createTable()

        log.info('db created')
    except Exception as e:
        log.exception('db_setup() - SQL ERROR: ' + str(e))
        exit(-1)


def setup():
    os.makedirs(data_path, exist_ok=True)

    setup_logging()
    setup_db()


if __name__ == '__main__':
    setup()

    log.info('Configured, starting...')
    # process various data for manipulation
    abbr.process()
    log.info("~" * 40)

    iana.process()
    log.info("~" * 40)
    
    geonames.process()
    log.info("~" * 40)

    # build any data sets we want
    topcities.build()

    log.info('Done!')
