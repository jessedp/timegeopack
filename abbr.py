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
abbr_type = "TT"
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


def process():
    raw_html = ''
    rows_sel = ''
    os.makedirs(dataPath(), exist_ok=True)

    log.info('Running abbreviation type: ' + abbr_type)

    if abbr_type == 'WIKI':
        rows_sel = "table.wikitable > tr"
        html_file = dataPath() + 'wiki_abbreviations.html'
        if (not os.path.isfile(html_file)):
            resp = get('https://en.wikipedia.org/wiki/List_of_time_zone_abbreviations',
                       headers={'Accept-Encoding': 'utf-8'})
            raw_html = resp.text
            f = open(html_file, 'w')
            f.write(raw_html)
            f.close()
        else:
            raw_html = open(html_file).read()
    elif abbr_type == 'TT':
        rows_sel = "table.infotable > tr"
        html_file = dataPath() + 'tt_abbreviations.html'
        if (not os.path.isfile(html_file)):
            resp = get('https://www.timetemperature.com/abbreviations/world_time_zone_abbreviations.shtml',
                       headers={'Accept-Encoding': 'utf-8'})
            raw_html = resp.text
            f = open(html_file, 'w')
            f.write(raw_html)
            f.close()
        else:
            raw_html = open(html_file).read()
    else:
        log.exception("UNKNOWN abbr_type [" + abbr_type + "], exiting...")
        exit(-1)

    log.info('Retrieved ' + abbr_type + ' source data')

    html = BeautifulSoup(raw_html, 'lxml')
    data = []
    off = ''
    # TODO: those 2 urls/providers happen to have the same row order... more/different cleanup for wikipedia likely required.
    for i, row in enumerate(html.select(rows_sel)):
        if i > 0:  # skip the header row
            cols = row.find_all('td')
            cols = [el.text.strip() for el in cols]
            if abbr_type == 'WIKI':
                # this is not going to work
                off = cols[2]
            elif abbr_type == 'TT':
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

            orig = cols[1].title()
            pieces = orig.split('(', 2)
            desc = pieces[0].strip()
            if len(pieces) == 2:
                desc_extra = pieces[1].strip(')(')
            else:
                desc_extra = ''

            data.append({'abbr': cols[0], 'desc': desc, 'desc_extra': desc_extra,
                         'offset': off, 'offset_sec': offsetToSec(off)})
    if log.isEnabledFor(logging.DEBUG):
        for x in data:
            log.debug("\t{}".format(x))

    insertRows(data)
