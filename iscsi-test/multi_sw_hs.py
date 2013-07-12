#!/usr/bin/python

from mininet.node import *
from mininet.log import setLogLevel, info, error
from mininet.net import Mininet
from mininet.topo import Topo, Node
from mininet.topolib import TreeTopo
from mininet.util import createLink
from mininet.cli import CLI
from mininet.node import UserSwitch
from netaddr import *


class TestTopo( Topo ):
    "Topology for a root switch with a HW interface connected to N switches and hosts."

    def __init__( self, N):

        # Add default members to class.
        super( TestTopo, self ).__init__()

        # Create switch and host nodes
        self.add_node( 1, Node( is_switch=1 ) )

        for num in range( 2, N+1 ):
            self.add_node( num, Node( is_switch=1 ) )
            self.add_edge( 1, num)
            self.add_node( N+1+num, Node( is_switch=0 ) )
            self.add_edge( num, N+1+num)

        # Consider all switches and hosts 'on'
        self.enable_all()


def setup(num, hwintf, beg_ip):

    info( '*** Creating network\n' )
    #net = Mininet( topo=TestTopo( num ), switch=UserSwitch, controller=RemoteController)
    #net = Mininet( topo=TestTopo( num ), controller=RemoteController, listenPort=6634)
    net = Mininet( topo=TestTopo( num ), controller=RemoteController)
    #net = Mininet( topo=TestTopo( num ))

    os.environ['NOX_CORE_DIR'] = '/opt/nox/bin'
    #controller = net.addController(name='c0', controller=NOX, noxArgs='switchqos --threads=1')
    controller = net.addController(name='c0', controller=NOX, noxArgs='switchqos --threads=10')
    #controller = net.addController(name='c0', controller=NOX, noxArgs='switch --threads=10')

    #os.environ['NOX_CORE_DIR'] = '/usr/local/bin'
    #controller = net.addController(name='c0', controller=NOX, noxArgs='switchqos')

    # Add HW interface to root switch
    switch = net.switches[ 0 ]
    switch.addIntf(hwintf)

    ip = beg_ip.split('.')
    for n in range( N-1 ):
        h = net.hosts[n]
        i = h.intfs[0]
        h.setIP(i, '.'.join(ip), 24)
        #print "IP: " + `h.IP()`
        ip[3] = str(int(ip[3]) + 1)
        #print h.IP()

    #import networkx
    #networkx.draw(net.topo.g)
    #import pylab
    #pylab.show()

    return(net)

def start(net):
    net.start()

    #for switch in net.switches:
    #    while not os.path.exists('/var/run/' + switch.name + '.sock'):
    #         #print '/var/run/' + switch.name + '.sock'
    #         time.sleep(1)
    time.sleep(5)
    for switch in net.switches:
        for i in switch.intfs.values():
            switch.updateMAC(i)


def test(net, mac, macs):
    if type(mac) == type(''):
        mac = int(EUI(mac))

    bad = 0
    #print "MAC: " + str(mac)
    N = len(net.hosts)
    m = 1
    while m <= macs:
        for n in range( N ):
            #print "n: %d m: %d macs: %d" % (n, m, macs)
            h = net.hosts[n]
            i = h.intfs[0]
            #print h.IP()
            #print h.MAC()
            MAC = "%012x" % (mac + m)
            #print "MAC: " + MAC
            MAC = EUI(MAC)
            MAC.dialect = mac_unix
            h.setMAC(i, str(MAC))
            print h.IP() + " -- " + h.MAC()  + " -- ",
            ret = h.cmd("ping -q -c1 10.10.20.6")
            if ret.find('1 packets transmitted, 1 received, 0% packet loss') != -1:
                print "OK"
            else:
                bad += 1
                print "BAD"
            m += 1

    return bad

if __name__ == '__main__':
    import time
    import os.path
    import os
    import sys

    if len(sys.argv) < 6:
        print "Usage: %s num_switches hw_intf beg_ip beg_mac num_macs"
        sys.exit(-1)

    #setLogLevel( 'debug' )
    setLogLevel( 'info' )

    N = int(sys.argv[1])
    itf = sys.argv[2]
    ip = sys.argv[3]
    mac = sys.argv[4]
    macs = int(sys.argv[5])
    net = setup(N, itf, ip)

    start(net)

    bad = test(net, mac, macs)
    print "Bad tests: " + `bad`

    #CLI( net )
    net.stop()


