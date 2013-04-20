#!/usr/bin/python

import os.path
import os
import sys
from qostester import *
from hp_bw import *

class HPQoSTester(QoSTester):
    hp_switch_ip = '10.10.10.11'
    hp_switch_login = 'root'
    hp_switch_passw = '123456'
    hp_switch_ssh_port = 22
    qos_interface_num = 20
    def test_setup(self):
    	print "Starting '/opt/nox-classic/bin/nox_core --libdir=/opt/nox-classic/lib -v -i ptcp:6633 switchqos > /tmp/nox.log 2>&1 &'"
   	code=os.system('cd /opt/nox-classic/bin/; /opt/nox-classic/bin/nox_core --libdir=/opt/nox-classic/lib -v -i ptcp:6633 switchqos > /tmp/nox.log 2>&1 &')
    	# how to determine really that NOX was correctly started?
	if code != 0:
            print stderr.read()
            sys.exit(1)
    def iscsi_test(self):
    	ssh=get_ssh(self.iscsi_test_ip)
    	stdin, stdout, stderr = ssh.exec_command("sudo /usr/local/bin/iscsi_test_2")
    	print "Disk I/O perf: "
    	print stderr.read()
    def test_cleanup(self):
    	print "Killing nox_core"
    	os.system('killall nox_core 2> /dev/null')
    def qos_setup(self,iscsi,traf):
	# log in the switch and set bandwidth-min for queues
    	client, chan = connect(host = self.hp_switch_ip, user = self.hp_switch_login, secret = self.hp_switch_passw, port = self.hp_switch_ssh_port)
    	bw_str = '%d %d' % (traf,iscsi)
	out = set_bw(chan, port=self.qos_interface_num, bw=bw_str)
        print "\nSetting bandwidth "+bw_str+"\n"	
	#print reduce(lambda x, y: x + y, out)
    	#out = get_bw(chan, port=self.qos_interface_num)
    	#print reduce(lambda x, y: x + y, out)
    	chan.close()
    	client.close()
    def perform_tests(self):
    	self.single_test(100,0)
    	self.single_test(80,20)
    	self.single_test(20,80)
    	self.single_test(0,100) # very slow

if __name__ == '__main__':
    
    server_ip = '10.10.20.102'
    server_ip_ssh = '127.0.0.1'
    client_ip = '10.10.20.103'
    client_ip_ssh = '192.168.122.13'
    iscsi_test_ip = '192.168.122.11'

    trafgen = IperfTrafGen(server_ip,server_ip_ssh,client_ip,client_ip_ssh)
    tester = HPQoSTester(trafgen,iscsi_test_ip)
    tester.perform_tests()
    tester.finish()

    #trafgen = SIPpTrafGen(server_ip,server_ip_ssh,client_ip,client_ip_ssh)
    #tester = HPQoSTester(trafgen,iscsi_test_ip)
    #tester.perform_tests()
    #tester.finish()

