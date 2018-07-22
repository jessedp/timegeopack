import os
import sqlite3
from bs4 import BeautifulSoup
from requests import get
import logging

import timegeopack as tgp
from util import offsetToSec


DEBUG = False
# TT = timetemperature.com
# WIKI = wikiepedia page - has extra info stuff that has to be stripped out :/
source = "TT"
log = logging.getLogger(__name__)


def dataPath():
    return tgp.data_path + 'abbr/'


def createTable():
    tgp.db().execute("CREATE TABLE IF NOT EXISTS abbreviations"
                          "(abbr STRING, desc STRING, desc_extra STRING, offset STRING, "
                          "offset_sec INTEGER, PRIMARY KEY(abbr, offset))")


def insertRows(data):
    db = tgp.db()
    cur = db.cursor()
    i = 0
    dupe = 0
    crit = 0

    for obj in data:
        try:
            cur.execute("INSERT INTO abbreviations (abbr, desc, desc_extra, offset, offset_sec) VALUES (?, ?, ?, ?, ?)",
                        (obj['abbr'], obj['desc'], obj['desc_extra'],
                         obj['offset'], obj['offset_sec'])
                        )
            i = i + 1
        except sqlite3.IntegrityError as e:
            log.debug(e)
            log.debug(obj)
            dupe = dupe + 1
        except sqlite3.OperationalError as e:
            log.critical(e)
            log.critical(obj)
            crit = crit + 1

    cur.close()
    db.commit()
    log.info('{:d} duplicate records'.format(dupe))
    log.info('{:d} critial records'.format(crit))
    log.info('Added {:d} records'.format(i))


providers = {
    'TT': {
        'url': 'https://www.timetemperature.com/abbreviations/world_time_zone_abbreviations.shtml',
        'filename': 'tt_abbreviations.html'
    },
    'WP': {
        'url': 'https://en.wikipedia.org/wiki/List_of_time_zone_abbreviations',
        'filename': 'wiki_abbreviations.html'
    }
}

def fetchData():
    log.info('Fetching abbreviation type: ' + source)
    html_file = dataPath() + providers[source]['filename']
    if (not os.path.isfile(html_file)):
        resp = get(providers['source']['url'],
                   headers={'Accept-Encoding': 'utf-8'})
        raw_html = resp.text
        f = open(html_file, 'w')
        f.write(raw_html)
        f.close()
    else:
        raw_html = open(html_file).read()

    return raw_html


def process(data_src='TT'):
    os.makedirs(dataPath(), exist_ok=True)

    global source
    if not data_src:
        source = data_src

    if source not in providers:
        log.exception("UNKNOWN source [" + source + "], exiting...")
        exit(-1)

    html = fetchData()
    log.info('Retrieved ' + source + ' source data')
    data = []
    if source == 'TT':
        data = parseTT(html)
    elif source == 'WP':
        data = parseWP(html)

    if log.isEnabledFor(logging.DEBUG):
        for x in data:
            log.debug("\t{}".format(x))
    insertRows(data)


def parseTT(html):
    html = BeautifulSoup(html, 'html.parser')
    data = []
    off = ''
    rows_sel = "table.infotable > tr"
    for i, row in enumerate(html.select(rows_sel)):
        if i > 0:  # skip the header row
            parts = []
            cols = row.find_all('td')
            cols = [el.text.strip() for el in cols]
            try:
                parts = cols[2].split(' ')
                if len(parts) != 3:
                    log.debug("Skipping abbr: " + cols[2])
                    continue

                sign = parts[1]
                tpars = parts[2].split(':')
                if (len(tpars) == 1):
                    off = sign + parts[2] + ':00'
                else:
                    off = sign + parts[2]
            except IndexError as e:
                log.info('cols:' + str(cols))
                log.info('parts:' + str(parts))
                log.exception(e)
                exit(-1)

            orig = cols[1].title()
            pieces = orig.split('(', 2)
            desc = pieces[0].strip()
            if len(pieces) == 2:
                desc_extra = pieces[1].strip(')(')
            else:
                desc_extra = ''

            data.append({'abbr': cols[0], 'desc': desc, 'desc_extra': desc_extra,
                         'offset': off, 'offset_sec': offsetToSec(off)})
    return data


def parseWP(html):
    log.critical('NOT FULLY IMPLEMENTED')
    html = BeautifulSoup(html, 'html.parser')
    data = []
    off = ''
    rows_sel = "table.wikitable > tr"
    # TODO: parsing columns needs to actually be done...
    for i, row in enumerate(html.select(rows_sel)):
        if i > 0:  # skip the header row
            cols = row.find_all('td')
            cols = [el.text.strip() for el in cols]
            # this is not going to work well
            off = cols[2]


            #data.append({'abbr': cols[0], 'desc': desc, 'desc_extra': desc_extra,
            #             'offset': off, 'offset_sec': offsetToSec(off)})
    
    return data