import abbr
import util

def testParsingTT():
    html = open('tests/data/tt_abbreviations.html').read()
    data = abbr.parseTT(html)

    last = data.pop()
    assert last['abbr'] == 'YEKST', 'last row abbr'
    assert last['desc'].lower() == 'YEKATERINBURG SUMMER TIME'.lower(), 'last row desc'
    #assert last['offset'] == 'UTC + 6', 'last row offset'
    #assert last['offset_sec'] == util.offsetToSec(last['offset']), 'last row offset_sec'

    #wtf is there not a shift?!?!?
    data.reverse()
    first = data.pop()

    assert first['abbr'] == 'A', 'first row abbr'
    assert first['desc'].lower() == 'ALPHA TIME ZONE'.lower(), 'first row desc'
    #assert first['offset'] == 'UTC + 1', 'first row offset'
