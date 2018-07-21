import os
import re
import requests
import shutil
import sqlite3
import logging
from zipfile import ZipFile

import timegeopack as tgp

DEBUG = False
log = logging.getLogger(__name__)

# Field Contants for geonames file
ID = 0
NAME = 1
ASCIINAME = 2
ALTNAME = 3
LAT = 4
LNG = 5
FCLASS = 6
FCODE = 7
CCODE = 8
CC2 = 9
ADMIN1 = 10
ADMIN2 = 11
ADMIN3 = 12
ADMIN4 = 13
POPUL = 14
ELEV = 15
DEM = 16
TZ = 17
MODDATE = 18


def dataPath():
    return tgp.data_path + 'geonames/'


def getGeonamesSql(table):
    """ Doing this just in case b/c they use the same format for varying sets """
    return "CREATE TABLE IF NOT EXISTS {} " \
           "(geonameid BIGINT PRIMARY KEY, name STRING, asciiname STRING, alternatenames STRING, " \
           "latitude STRING, longitude STRING, feature_class STRING, feature_code STRING, " \
           "country_code STRING, cc2 STRING, admin1_code STRING, admin2_code STRING, admin3_code STRING, " \
           "admin4 code STRING, population BIGINT, elevation BIGINT, dem STRING, timezone STRING, " \
           "modification_date STRING)".format(table)


def getAdminCodesSql():
    return "CREATE TABLE IF NOT EXISTS admin1codes " \
           "(country_code STRING, code STRING, name STRING, PRIMARY KEY(country_code, code))"


def getCountryInfoSql():
    return "CREATE TABLE IF NOT EXISTS countryinfo " \
           "(iso STRING PRIMAY KEY, iso3 STRING, iso_numeric STRING, fips STRING, country STRING, capital STRING, " \
           "area BIGINT, population BIGINT, continent STRING, tld STRING, currencycode STRING," \
           "currencyname STRING, phone STRING, postal_code_fmt STRING, postal_code_regex STRING, " \
           "languages STRING, geonameid BIGINT, neighbours STRING, equivalentfipscode STRING)"


def createTables():
    tgp.db().execute(getGeonamesSql('geonames'))
    tgp.db().execute(getAdminCodesSql())
    tgp.db().execute(getCountryInfoSql())


def processCities():
    db = tgp.db()
    cur = db.cursor()
    i = 0
    dupe = 0
    crit = 0
    row = ''
    with open(dataPath() + 'cities15000.txt') as file:
        for line in file:
            try:
                fields = re.split(r'\t', line.strip())
                row = list(map(str.strip, fields))
                cur.execute("INSERT INTO geonames VALUES "
                            "(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                            row)
                i = i + 1
            except sqlite3.IntegrityError as e:
                log.debug(e)
                log.debug(row)
                dupe = dupe + 1
            except sqlite3.OperationalError as e:
                log.critical(e)
                log.critical(row)
                crit = crit + 1

    cur.close()
    db.commit()
    log.info('cities - {:d} duplicate records'.format(dupe))
    log.info('cities - {:d} critial records'.format(crit))
    log.info('cities - Added {:d} records'.format(i))


def processAdminCode():
    """ only bothering with admin codes 1"""
    db = tgp.db()
    cur = db.cursor()
    i = 0
    dupe = 0
    crit = 0
    row = ''
    with open(dataPath() + 'admin1CodesASCII.txt') as file:
        for line in file:
            try:
                fields = re.split(r'\t', line.strip())
                row = list(map(str.strip, fields))
                parts = row[0].split('.', 2)
                cur.execute("INSERT INTO admin1codes VALUES "
                            "(?, ?, ?)",
                            (parts[0], parts[1], row[1]))
                i = i + 1
            except sqlite3.IntegrityError as e:
                log.debug(e)
                log.debug(row)
                dupe = dupe + 1
            except sqlite3.OperationalError as e:
                log.critical(e)
                log.critical(row)
                crit = crit + 1

    cur.close()
    db.commit()
    log.info('admin1 - {:d} duplicate records'.format(dupe))
    log.info('admin1 - {:d} critial records'.format(crit))
    log.info('admin1 - Added {:d} records'.format(i))


def processCountryInfo():
    """ only bothering with admin codes 1"""
    db = tgp.db()
    cur = db.cursor()
    i = 0
    dupe = 0
    crit = 0
    row = ''
    with open(dataPath() + 'countryInfo.txt') as file:
        for line in file:
            try:
                if line.startswith('#'):
                    continue

                fields = re.split(r'\t', line)
                row = list(map(str.strip, fields))

                cur.execute("INSERT INTO countryinfo VALUES "
                            "(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", row)
                i = i + 1
            except sqlite3.IntegrityError as e:
                log.debug(e)
                log.debug(row)
                dupe = dupe + 1
            except sqlite3.OperationalError as e:
                log.critical(e)
                log.critical(row)
                crit = crit + 1

    cur.close()
    db.commit()
    log.info('country - {:d} duplicate records'.format(dupe))
    log.info('country - {:d} critial records'.format(crit))
    log.info('country - Added {:d} records'.format(i))


def stageFiles():
    os.makedirs(dataPath(), exist_ok=True)
    files = ['cities15000.zip', 'admin1CodesASCII.txt', 'countryInfo.txt']
    for file in files:
        if not os.path.exists(dataPath() + file):
            log.info("No data file found, retrieving")
            url = "http://download.geonames.org/export/dump/{}".format(file)
            log.info(url)
            r = requests.get(url, stream=True)

            if r.status_code == 200:
                with open(dataPath() + file, 'wb') as f:
                    r.raw.decode_content = True
                    shutil.copyfileobj(r.raw, f)
            else:
                log.exception('Unable to download from:' + url)
                exit(-1)
        else:
            log.info("[{}] found".format(file))

        if file.endswith('.zip'):
            with ZipFile(dataPath() + file, 'r') as data:
                data.extractall(dataPath())

    log.info("Data extracted")


def process():
    stageFiles()
    processCities()
    processAdminCode()
    processCountryInfo()
