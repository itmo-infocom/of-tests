#!/usr/bin/python

import paramiko
import sys
import select

def connect(host = '10.10.10.13', user = 'root', secret = '123456', port = 22):

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=user, password=secret, port=port)

    chan = client.invoke_shell()
    chan.settimeout(0.0)

    sw_rd(chan)
    chan.send('\n')
    sw_rd(chan)
    #chan.send('show version\n')
    #sw_rd(chan)

    return client, chan
    
def sw_rd(chan):
    out = ''
    r, w, e = select.select([chan, sys.stdin], [], [])

    if chan in r:
        try:
            x = chan.recv(1024)
            if len(x) == 0:
                return x
            out += x
        except socket.timeout:
            pass

    return x

def set_bw(chan, port=20, bw='50 50 0 0 0 0 0 0'):
    import types

    out = []
    if type(port) == types.StringType:
        port = int(port)
    if type(bw) == types.ListType or type(bw) == types.TupleType:
        bw = reduce (lambda x, y: str(x) + ' ' + str(y), bw)

    chan.send('config\n')
    out.append(sw_rd(chan))
    chan.send('int %d bandwidth-min output %s\n' % (port, bw))
    out.append(sw_rd(chan))

    return out

def get_bw(chan, port=20):
    out = []
    chan.send('show bandwidth output %d\n' % port)
    out.append(sw_rd(chan))
    out.append(sw_rd(chan))

    return out

if __name__ == '__main__':
    import sys

    if len(sys.argv) != 11:
        print "Usage: %s [user[:pwd]@]host[:port] port bw1 ... bw8" % sys.argv[0]
        sys.exit(-1)

    hostname = sys.argv[1]
    args = []
    if hostname.find('@') >= 0:
        username, hostname = hostname.split('@')
        if username.find(':') >= 0:
            username,secret = username.split(':')
            args += "secret='" + secret + "',"
        args += "user='" + username + "',"
    if hostname.find(':') >= 0:
        hostname, port = hostname.split(':')
        args += "port=" + port + ","

    args += "host='" + hostname + "'"

    cmd = 'connect(' + ''.join(args) + ')'
    print cmd
    client, chan = eval(cmd)

    out = set_bw(chan, port=sys.argv[2], bw=' '.join(sys.argv[3:]))
    print reduce(lambda x, y: x + y, out)
    out = get_bw(chan)
    print reduce(lambda x, y: x + y, out)

    chan.close()
    client.close()

