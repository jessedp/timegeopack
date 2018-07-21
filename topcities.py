import os
import glob
import logging
import sqlite3

import timegeopack as tgp
import geonames as gn

log = logging.getLogger(__name__)
db = None

OUT_SQL = True
OUT_TAB = True
OUT_SPLITFILE = True

# these ARE NOT in geonames (g) - they are joined tables
REGION = 19
CTRYNAME = 20


def dataPath():
    return tgp.data_path + 'cities/'


def createTable():
    tgp.db().execute("CREATE TABLE IF NOT EXISTS topcities"
                          "(geonameid STRING PRIMARY KEY, name STRING, asciiname STRING, "
                          "latitude STRING, longitude STRING, country_code STRING, admin1_code STRING, "
                          "population BIGINT, timezone STRING, region STRING, country_name STRING)")


def insertRow(row):
    global db
    cur = db.cursor()
    try:
        cur.execute("INSERT INTO topcities (geonameid, name, asciiname, latitude, longitude, country_code, "
                    "admin1_code, population, timezone, region, country_name) VALUES"
                    " (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", row)
    except sqlite3.IntegrityError as e:
        log.debug(e)
        log.debug(row)
    except sqlite3.OperationalError as e:
        log.critical(e)
        log.critical(row)

    cur.close()
    db.commit()


def _record(needle, haystack, row):

    if needle not in haystack:
        if OUT_SPLITFILE:
            new = list(row)
            out = open(dataPath() + row[gn.TZ].replace('/', '_') + '.txt', 'a')
            del new[gn.ALTNAME]
            out.write("\t".join(map(str, row)) + "\n")
            out.close()

        data = []
        data.append(row[gn.ID])
        data.append(row[gn.NAME])
        data.append(row[gn.ASCIINAME])
        data.append(row[gn.LAT])
        data.append(row[gn.LNG])
        data.append(row[gn.CCODE])
        data.append(row[gn.ADMIN1])
        data.append(row[gn.POPUL])
        data.append(row[gn.TZ])
        data.append(row[REGION])
        data.append(row[CTRYNAME])

        if OUT_TAB:
            out = open(dataPath() + 'topcities.txt', 'a')
            out.write("\t".join(map(str, data)) + "\n")
            out.close()

        if OUT_SQL:
            insertRow(data)


def build():
    os.makedirs(dataPath(), exist_ok=True)
    global db
    db = tgp.db()

    cur = db.cursor()
    for i in glob.glob(u'{}*.txt'.format(dataPath())):
        os.unlink(i)

    all_tz_sql = "select distinct timezone from geonames"
    cur.execute(all_tz_sql)
    alltz = cur.fetchall()

    MAX_CITY = 30

    cities = {}
    pops = {}

    SQL_SELECT = "select g.*, a.name, c.country from geonames g " \
                 "left join admin1codes a on g.country_code = a.country_code and g.admin1_code = a.code " \
                 "left join countryinfo c on g.country_code = c.iso "

    # set population baselines using capital(s)
    # ignore the MAX checks here, b/c the shouldn't happen
    log.info("Load capitals (PPLC) for each zone if they exist")
    for tz in alltz:
        cur_tz = tz[0]
        sql = SQL_SELECT + " where feature_code in ('PPLC') and timezone = '{}' " \
                           "order by feature_code desc, population desc".format(
                               cur_tz)
        pplcs = cur.execute(sql)
        for pplc in pplcs:
            # gather population nums
            if cur_tz not in pops:
                pops[cur_tz] = {}
                pops[cur_tz]['total'] = pplc[gn.POPUL]
                pops[cur_tz]['pplc'] = pplc[gn.POPUL]
                pops[cur_tz]['max'] = pplc[gn.POPUL]
            else:
                pops[cur_tz]['total'] = pops[cur_tz]['total'] + pplc[gn.POPUL]
                # capture pplc pop
                if pplc[gn.POPUL] > pops[cur_tz]['pplc']:
                    pops[cur_tz]['pplc'] = pplc[gn.POPUL]
                # set the max pop
                if pplc[gn.POPUL] > pops[cur_tz]['max']:
                    pops[cur_tz]['max'] = pplc[gn.POPUL]

            # prime the files (this should be in one place)
            if cur_tz not in cities:
                cities[cur_tz] = {}

            _record(pplc[gn.ID], cities[cur_tz], pplc)
            cities[cur_tz][pplc[gn.ID]] = pplc[gn.NAME]

    # set population baselines using max pop
    # ignore the MAX checks here, b/c they shouldn't happen
    log.info(
        "Load the city with the largest population for each zone (skip if it's the PPLC)")
    for tz in alltz:
        cur_tz = tz[0]
        sql = SQL_SELECT + \
            " where timezone = '{}' order by population desc limit 1".format(
                cur_tz)
        maxes = cur.execute(sql)
        for max in maxes:
            # create the rec or if the pplc was the max, we have it, keep going
            if cur_tz not in cities:
                cities[cur_tz] = {}
            elif max[gn.ID] in cities[cur_tz]:
                continue

            # gather population nums
            if cur_tz not in pops:
                pops[cur_tz] = {}
                pops[cur_tz]['total'] = max[gn.POPUL]
                pops[cur_tz]['pplc'] = 0
                pops[cur_tz]['max'] = max[gn.POPUL]
            elif max[gn.POPUL] > pops[cur_tz]['max']:
                pops[cur_tz]['max'] = max[gn.POPUL]
                pops[cur_tz]['total'] += max[gn.POPUL]
            else:
                pops[cur_tz]['total'] += max[gn.POPUL]

            # prime the files (this should be in one place)
            if cur_tz not in cities:
                cities[cur_tz] = {}

            _record(max[gn.ID], cities[cur_tz], max)
            cities[cur_tz][max[gn.ID]] = max[gn.NAME]

    # fill in above the PPLC as necessary (max pop > pplc pop)
    log.info("Filling in all cities larger than the PPLC")
    for tz in pops:
        if pops[tz]['pplc'] == 0 or pops[tz]['max'] <= pops[tz]['pplc']:
            continue

        city_left = MAX_CITY - len(cities[tz])
        sql = SQL_SELECT + " where g.timezone = '{}' and g.population > {} and g.feature_code != 'PPLX' " \
                           "order by g.population desc limit {}".format(
                               tz, pops[tz]['pplc'], city_left)
        recs = cur.execute(sql)
        for rec in recs:
            # prime the files (this should be in one place)
            if tz not in cities:
                cities[tz] = {}

            _record(rec[gn.ID], cities[tz], rec)
            cities[tz][rec[gn.ID]] = rec[gn.NAME]

    # fill in below the PPLC (< pplc pop, *some* percentage of pop)
    log.info("Fill in cities smaller than the PPLC up to {}".format(MAX_CITY))
    for tz in pops:
        if pops[tz]['pplc'] >= pops[tz]['max']:
            pop = pops[tz]['pplc']
            pct = 0.25
        elif pops[tz]['pplc'] != 0:  # we had a max
            pop = pops[tz]['max']
            pct = 0.5
        else:
            pop = pops[tz]['max']
            pct = 0.35

        log.debug("{} : max = {} pplc = {} | pop = {}  pct = {}".format(
            tz, pops[tz]['max'], pops[tz]['pplc'], pop, pct))
        city_left = MAX_CITY - len(cities[tz])
        sql = SQL_SELECT + "where g.timezone = '{}' and g.population < {} and g.population > {} * {} " \
            "and g.feature_code != 'PPLX' order by g.population desc limit {}".format(
                tz, pop, pop, pct, city_left)

        recs = cur.execute(sql).fetchall()

        # often the max pop cities are way larger than other cities we want to include
        if len(recs) < 3:
            low_pop = 100000
            sql = SQL_SELECT + "where g.timezone = '{}' and g.population > {} " \
                "and g.feature_code != 'PPLX' order by g.population desc limit {}".format(
                    tz, low_pop, city_left)

            recs = cur.execute(sql)

        for rec in recs:
            # prime the files (this should be in one place)
            if tz not in cities:
                cities[tz] = {}

            _record(rec[gn.ID], cities[tz], rec)
            cities[tz][rec[gn.ID]] = rec[gn.NAME]

    log.info("Generating overview(s)")
    out = open(dataPath() + 'city_overview.tab', 'w')
    tot = 0
    for tz in cities:
        row = []
        row.append(tz)
        row.append(str(len(cities[tz])))
        tot += len(cities[tz])
        s = "\t".join(row)
        log.debug(s)
        out.write(s + "\n")
    s = "\t\t\tTotal = {}".format(tot)
    log.debug(s)
    out.write(s + "\n")
    out.close()


if __name__ == '__main__':
    tgp.setup_logging()
    os.makedirs(dataPath(), exist_ok=True)
    build()
