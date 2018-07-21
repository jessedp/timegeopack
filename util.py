def offsetToSec(str):
    neg = False
    time = ""
    if (str.startswith('-') or str.startswith('+')):
        time = str[1:]
        if str.startswith('-'):
            neg = True
    else:
        time = str

    parts = time.split(':')
    if len(parts) == 1:
        parts.append(0)
    secs = int(parts[0]) * 3600 + int(parts[1])
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
