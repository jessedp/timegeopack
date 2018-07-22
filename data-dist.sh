#!/usr/bin/env bash
cd data
/usr/bin/zip -q timegeopack.sqlite3.zip timegeopack.sqlite3
cd cities
cat *.txt > all_cities.txt
/usr/bin/zip -q timegeopack.topcities.zip *