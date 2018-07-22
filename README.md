[![Build Status](https://travis-ci.org/jessedp/timegeopack.svg?branch=master)](https://travis-ci.org/jessedp/timegeopack)

### TimeGeoPack
Semi-automatically gather public geographic and time-related data together 
to provide a quick start for mashing up various combinations of the data 
or playing with non directly queryable data sets to suit your needs 
(see the sample). 

Nothing here is intended to assist with date/time calculations because **that**
would be **super** redundant.


Run the script:
```angular2html
# python3 timegeopack.py
```
and it will:
* download the most recent versions of the supported data soures (below) 
* parse/process the data and stick it into a sqlite3 database
* run a sample script to generate a custom data set

Alternately! Everything mentioned here is available zipped up in the [current release](https://github.com/jessedp/timegeopack/releases/latest) including:
* the generated sqlite db
* the sample top cities (by timezone and cat'd together ... plus some summary)


#### requirements
* python 3 (developed using 3.6.5)
* _suggested_ - a db browser/editor/etc gui [DB Browser for SQLite](http://sqlitebrowser.org/) is pretty handy


#### data sources used
* [GeoNames](http://www.geonames.org/) - a huge amount of geographical data that also
includes most of the timezone relate info needed. Currently pulled:
    * **cities15000.txt** - a subset of the full main data file the only contains cities with populations over 15k
    * **admin1CodesASCII.txt** - admin divisions - think states, provinces, and the such
    * **countryInfo.txt** - the full country name plus tons of other country specific data
    * these are in the _geonames_, _admin1codes_, and _countryinfo_ tables, respectively
    * timeZones.txt is not include b/c IANA was already there and the DST values are awkward
    to update (columns contain the year name)
* [IANA Time Zone Database](https://www.iana.org/time-zones) - parsed out into the _timezones_ table.
    * most of this is in the GeoNames database
    * _rules_ still neeed to be included
* Abbreviations - the _Human_ versions that everyone knows and references (EST, PDT, Central European Time, Mountain Time, etc.).
    * currently from [TimeTemperature.com](https://www.timetemperature.com/abbreviations/world_time_zone_abbreviations.shtml)
    
    
#### Why? Or, examples, please?
1. Say using Abbreviations (let someone pick 'Eastern Standard Time') 
so you can store 'America/New_York' in your application.  
2. Take that a step further and allow someone to also search for a city to do the same.
    * Yes, that's a fairly direct lookup but will require an ajax/whatever call 
    (even the 15k geonames data is >6mb, you're not doing that server side)
3. Be creative even if the majority of it is combining the geonames data you may not 
    have know about together
    
#### A sample - _topcities.py_
Consider **#2** above and let's do that client-side. There's a [javascript here](https://github.com/thejohnhoffer/ttzc) that does what we need
and, as linked there, a working version of it can be fouond at [The Time Zone Converter](http://www.thetimezoneconverter.com/).

Great, use that. But, where does that data come from??? Check out the source - 
there are some crazy datasets involved. I have no idea where they got it 
from, but the data here (actually just the geonames) will get it for you. 
And, say you started using that and wanted to keep it updated, easily tweak
what can be searched, or maybe limit the data avaiable to a certain country,
continent, etc.

So - the included **topcities.py** gets you pretty close to a programatically 
curated base to generate the dataset off of. It basically:
* Ensures the Capital is always included. This is weird b/c it's the capital for the nation, 
but only if it's in the time zone you're looking at.
    * Example: Washington DC shows as a Capital in America/New_York - 
    America/Chicago, America/Denver, etc. show no _main_ capital
* Picks up to 30 of the largest cities per zone.            
    
    


##### Thanks:
* makes used of a slightly modified version of [tz2js](https://github.com/nzlosh/tz2js) by nzlosh
* and, you know, all the data sources menetioned