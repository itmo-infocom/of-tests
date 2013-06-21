#!/usr/bin/python

import re
import shlex, subprocess
import math

tsum=0;
tsum2=0;
count=0;

def rtt_measure(num, size=512, device="/dev/raw/raw1"):
    pt = re.compile('Time for all .* commands was ([0-9.]*) secs,')
    times=[]
    tsum=0

    for i in range(num):
        args="sg_read blk_sgio=1 time=1 bpt=1 dio=1 if=%s count=1 bs=%d" % \
            (device, size)
        args=shlex.split(args)
        p = subprocess.Popen(args, stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        (out, err)=p.communicate()

        #print "o: " + out
        #print "e: " + err

        if p.returncode:
            raise OSError, err
        else:
            res = pt.match(err)
            if (res):
                time=res.group(1)
                time = float(time)
                #print "t: %f" % time
                times.append(time)
                tsum += time

    latency = tsum / num
    jitter = 0

    for time in times:
        time = latency - time
        jitter += time * time

    jitter = math.sqrt(jitter/num);

    return (latency, jitter)

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 4:
        print "Usage: %s device packages sizes..."
        sys.exit()
    
    dev = sys.argv[1]
    num = int(sys.argv[2])

    for size in sys.argv[3:]:
        size = int(size)
        (l,j) = rtt_measure(num, size, dev)
        print "Size=%d Packets=%d Latency=%f Jitter=%f\n" % (size, num, l, j)
