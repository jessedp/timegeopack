#!/usr/bin/env bash
cd data
/usr/bin/zip -q timegeopack.sqlite3.zip timegeopack.sqlite3
cd cities
/usr/bin/zip -q timegeopack.topcities.zip *