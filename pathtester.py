#!/usr/bin/python

import os.path
import os
import sys
from hp_bw import *
import time

def get_ssh(host):
    ssh=paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username="openflow", password="openflow")
    return ssh

class PathTester:
    hp_switch_ip = '10.10.10.11'
    hp_switch_login = 'root'
    hp_switch_passw = '123456'
    hp_switch_ssh_port = 22
    ping_from_ip = '192.168.122.11'
    ping_to_ip = '10.10.20.6'
    
    def test_setup(self):
    	self.pinger=get_ssh(self.ping_from_ip)
        self.sw_client, self.sw_chan = connect(host = self.hp_switch_ip, user = self.hp_switch_login, secret = self.hp_switch_passw, port = self.hp_switch_ssh_port)
        self.sw_chan.send('config\n')
        #print sw_rd(self.sw_chan)
        #self.mod_iface(17,'enable')
	#self.mod_iface(18,'enable')
	time.sleep(5)
	print "Starting '/opt/nox-classic/bin/nox_core --libdir=/opt/nox-classic/lib -v -i ptcp:6633 switchqos > /tmp/nox.log 2>&1 &'"
   	code=os.system('cd /opt/nox-classic/bin/; /opt/nox-classic/bin/nox_core --libdir=/opt/nox-classic/lib -v -v -i ptcp:6633 switch > /tmp/nox.log 2>&1 &')	
	if code != 0:
            print stderr.read()
            sys.exit(1)
	time.sleep(10)
        self.mod_iface(19,'enable')
	self.mod_iface(20,'enable')
	self.started = 1

    def ping_test(self):
    	stdin, stdout, stderr = self.pinger.exec_command("ping -c 30 "+self.ping_to_ip)
    	print stdout.read()
    	time.sleep(10)

    def test_cleanup(self):
    	print "Killing nox_core"
    	os.system('killall nox_core 2> /dev/null')
	if self.started == 1:
    	    self.pinger.close()
    	    self.sw_client.close()
    	    self.sw_chan.close()
        
    def mod_iface(self,port,mod):
	command = 'int %d %s\n' % (port, mod)
    	self.sw_chan.send(command)	
    	print command
	time.sleep(10)

    def perform_tests(self):
	self.started = 0
	self.test_cleanup()
	self.test_setup()
	#raw_input("Press Enter to continue...")
    	self.ping_test()
    	self.mod_iface(19,'disable')
    	self.ping_test()
	#raw_input("Press Enter to continue...")
    	self.mod_iface(19,'enable')
    	self.ping_test()
	#raw_input("Press Enter to continue...")
    	self.mod_iface(20,'disable')
    	self.ping_test()
    	self.test_cleanup()
    	
if __name__ == '__main__':
    tester = PathTester()
    tester.perform_tests()
