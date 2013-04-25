#!/usr/bin/python

import os.path
import os
import sys
from qostester import *

class SoftQoSTester(QoSTester):
    sleep_timeout = 3
    def test_setup(self):
	print "Starting 'ofdatapath -v -i eth1,eth2 punix:/var/run/s1.sock > /tmp/s1-ofd.log 2>&1 &'"
    	os.system('ofdatapath -v -i eth1,eth2 punix:/var/run/s1.sock > /tmp/s1-ofd.log 2>&1 &')
    	print "Starting 'ofprotocol unix:/var/run/s1.sock tcp:127.0.0.1:6633 > /tmp/s1-ofp.log 2>&1 &'"
    	os.system('ofprotocol unix:/var/run/s1.sock tcp:127.0.0.1:6633 > /tmp/s1-ofp.log 2>&1 &')
    	print "Starting '/usr/local/bin/nox_core --libdir=/usr/local/lib -v -i ptcp:6633 switchqos > /tmp/nox.log 2>&1 &'"
   	os.system('cd /usr/local/bin/; /usr/local/bin/nox_core --libdir=/usr/local/lib -v -i ptcp:6633 switchqos > /tmp/nox.log 2>&1 &')
    	while not os.path.exists('/var/run/s1.sock'):
            time.sleep(1)
    def iscsi_test(self):
    	ssh=get_ssh(self.iscsi_test_ip)
    	stdin, stdout, stderr = ssh.exec_command("sudo /usr/local/bin/iscsi_test")
    	print "Disk I/O perf: "
    	print stderr.read()
    def test_cleanup(self):
    	print "Killing ofprotocol ofdatapath nox_core"
    	os.system('killall ofprotocol ofdatapath nox_core 2> /dev/null')
    	os.system('ifconfig eth1 down; ifconfig eth2 down')
    def qos_setup(self,iscsi,traf):
        print "QoS: iSCSI=%d TRAF=%d" % (iscsi, traf)
        os.system('dpctl unix:/var/run/s1.sock queue-mod 1 1 %d > /tmp/s1-queue.log' % traf)
        os.system('dpctl unix:/var/run/s1.sock queue-mod 1 2 %d >> /tmp/s1-queue.log' % iscsi)
        os.system('dpctl unix:/var/run/s1.sock queue-mod 2 1 %d >> /tmp/s1-queue.log' % traf)
        os.system('dpctl unix:/var/run/s1.sock queue-mod 2 2 %d >> /tmp/s1-queue.log' % iscsi)
        os.system('dpctl unix:/var/run/s1.sock queue-mod 1 3 %d >> /tmp/s1-queue.log' % traf)
        os.system('dpctl unix:/var/run/s1.sock queue-mod 2 3 %d >> /tmp/s1-queue.log' % traf)
    def perform_tests(self):
    	self.single_test(1000,0)
    	self.single_test(1,1000)
    	self.single_test(1000,1)
    	self.single_test(1000,1000)
    	self.single_test(1,1)

if __name__ == '__main__':
    
    server_ip = '10.10.10.102'
    server_ip_ssh = '192.168.122.12'
    client_ip = '10.10.10.104'
    client_ip_ssh = '192.168.122.13'
    iscsi_test_ip = '192.168.122.11'

    trafgen = IperfTrafGen(server_ip,server_ip_ssh,client_ip,client_ip_ssh)
    tester = SoftQoSTester(trafgen,iscsi_test_ip)
    tester.perform_tests()
    tester.finish()

    trafgen = SIPpTrafGen(server_ip,server_ip_ssh,client_ip,client_ip_ssh)
    tester = SoftQoSTester(trafgen,iscsi_test_ip)
    tester.perform_tests()
    tester.finish()
