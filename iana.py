import os
import re
import shutil
import tempfile
import tarfile
import sqlite3
import urllib.request
import tz2js
import logging

import timegeopack as tgp
import util

DEBUG = False
log = logging.getLogger(__name__)


def createTable():
    tgp.db().execute("CREATE TABLE IF NOT EXISTS timezones"
                          "(timezone STRING PRIMARY KEY, offset STRING, offset_sec INTEGER)")


def insertRows(data):
    db = tgp.db()
    cur = db.cursor()
    i = 0
    dupe = 0
    crit = 0
    for k, v in data['zones'].items():
        for x, y in v.items():
            rec = y[0]
            zone = ''
            if x is None:
                # log.info(rec.getArea())
                zone = rec.getArea()
            else:
                zone = rec.getArea() + '/' + x
            try:
                cur.execute("INSERT INTO timezones (timezone, offset, offset_sec) VALUES (?, ?, ?)",
                            (zone, rec.getGMTOffset(),
                             util.secToOffset(rec.getGMTOffset()))
                            )
                i = i + 1
            except sqlite3.IntegrityError as e:
                log.info(e)
                log.info(rec)
                dupe = dupe + 1
            except sqlite3.OperationalError as e:
                log.critical(e)
                log.critical(rec)
                crit = crit + 1

    cur.close()
    db.commit()
    log.info('{:d} duplicate records'.format(dupe))
    log.info('{:d} critial records'.format(crit))
    log.info('Added {:d} records'.format(i))


def dataPath():
    return tgp.data_path + 'iana/'


def process():
    stageFiles()
    # parseOlsonFiles()
    processTzData()


def parseMakefile(str):
    find = re.search("PRIMARY_YDATA=(.*?)YDATA", str, re.DOTALL)
    list = find.group(1).replace("\\", '').strip()
    parts = re.split("\s+", list)
    parts.append('etcetera')
    # parts.append('backzone')
    return parts


def stageFiles():
    os.makedirs(dataPath(), exist_ok=True)

    with urllib.request.urlopen('ftp://ftp.iana.org/tz/data/version') as resp:
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            shutil.copyfileobj(resp, tmp_file)

    pub_ver = open(tmp_file.name).read().strip()
    os.unlink(tmp_file.name)

    log.info('Published Version: ' + pub_ver)
    cur_ver = ''
    if os.path.exists(dataPath() + 'version'):
        cur_ver = open(dataPath() + 'version').read().strip()

    log.info('Our Version: ' + cur_ver)

    # TODO: This is 100% assuming anything public that's different is what we want.
    if pub_ver == cur_ver:
        log.info('Data up to date, carrying on.')
    else:
        log.info('Out of date, need to retrive current files')

        with urllib.request.urlopen('ftp://ftp.iana.org/tz/tzdata-latest.tar.gz') as resp:
            with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                shutil.copyfileobj(resp, tmp_file)

                tar = tarfile.open(tmp_file.name, "r:gz")
                tar.extractall(dataPath())

                for member in tar.getmembers():
                    log.info(
                        "file: {} - {} bytes - {}".format(member.name, member.size, member.mtime))

                log.info('Retrieved and extracted current current data archive')
        os.unlink(tmp_file.name)


def processTzData():
    tz2js.tzpath = dataPath()
    data = tz2js.parseZoneFile()
    insertRows(data)
