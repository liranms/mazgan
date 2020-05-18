import re
import sys
for line in sys.stdin:
        line = line.strip()
        r = re.findall(r"(pulse|space) (\d+)", line)
        if r:
                r = r[0]
                n = int(r[1])
                if n in xrange(600, 800):
                        n = 700
                if n in xrange(1600, 1800):
                        n = 1700
                line = "%s %d" % (r[0], n)
        print line