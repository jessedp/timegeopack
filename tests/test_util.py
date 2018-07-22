import util

def testoffToSec():
    assert util.offsetToSec('0') == 0
    assert util.offsetToSec(0) == 0

    assert util.offsetToSec('1') == 3600
    assert util.offsetToSec('1:00') == 3600
    assert util.offsetToSec('+1') == 3600
    assert util.offsetToSec('+1:00') == 3600

    assert util.offsetToSec(-1) == -3600
    assert util.offsetToSec("-1") == -3600
    assert util.offsetToSec("-1:00") == -3600

    assert util.offsetToSec("+5:45") == 20700


def testsecToOffset():
    assert util.secToOffset('0') == '0:00'
    assert util.secToOffset(0) == '0:00'

    assert util.secToOffset(3600) == "+1:00"
    assert util.secToOffset(-3600) == "-1:00"

    assert util.secToOffset(20700) == "+5:45"

