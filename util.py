def offsetToSec(offset):
    offset = str(offset)
    neg = False
    time = ""
    if (offset.startswith('-') or offset.startswith('+')):
        time = offset[1:]
        if offset.startswith('-'):
            neg = True
    else:
        time = offset

    parts = time.split(':')
    if len(parts) == 1:
        parts.append(0)
    secs = int(parts[0]) * 3600 + int(parts[1]) * 60
    if (neg):
        secs = secs * -1

    return secs


def secToOffset(sec):
    num = int(sec) / 60.0 / 60.0
    numstr = str(num)
    parts = numstr.split(".")
    if (num > 0):
        offstr = "+{}:".format(parts[0])
    else:
        offstr = "{}:".format(parts[0])

    min = 60 * (num - int(parts[0]))
    offstr = offstr + "{:02}".format(int(min))
    return offstr
