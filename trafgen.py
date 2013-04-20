#!/usr/bin/python

import paramiko
from multiprocessing import Process

def get_ssh(host):
    ssh=paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username="openflow", password="openflow")
    return ssh

class TrafGen:
    def __init__(self,hosts,hosts_ssh,hostc,hostc_ssh):
	self.hosts = hosts
	self.hosts_ssh = hosts_ssh
	self.hostc = hostc
	self.hostc_ssh = hostc_ssh
    def start_server(self):
	pass
    def start_client(self):
	pass
    def run_server_process(self):
	self.server_process = Process(target=self.start_server)
	self.server_process.start()
    def run_client_process(self):
	self.client_process = Process(target=self.start_client)
	self.client_process.start()
    def stop_server(self):
	pass
    def stop_client(self):
	pass

class IperfTrafGen(TrafGen):
    killall = "killall iperf"
    def start_server(self):
	ssh=get_ssh(self.hosts_ssh)
	print "starting Iperf server: "+self.hosts_ssh
    	stdin, stdout, stderr = ssh.exec_command("iperf -s")
    	print stderr.read()
    def start_client(self):
    	ssh=get_ssh(self.hostc_ssh)
    	stdin, stdout, stderr = ssh.exec_command("iperf -t 9999 -c " + self.hosts + " ")
   	print stdout.read()
    	print stderr.read()
    def stop_server(self):
        ssh=get_ssh(self.hosts_ssh)
    	stdin, stdout, stderr = ssh.exec_command(self.killall)
    	self.server_process.terminate()
    def stop_client(self):
    	ssh=get_ssh(self.hostc_ssh)
    	stdin, stdout, stderr = ssh.exec_command(self.killall)
    	self.client_process.join()
    	self.client_process.terminate()

class SIPpTrafGen(TrafGen):
    killall = "sudo killall sipp"
    def start_server(self):
	ssh=get_ssh(self.hosts_ssh)
    	stdin, stdout, stderr = ssh.exec_command("cd sipp-3.3; ./sipp -sn uas -i " + self.hosts + " -bg > ~/sipp-serv.log 2>&1 &")
    	print stderr.read()
    def start_client(self):
    	ssh=get_ssh(self.hostc_ssh)
    	stdin, stdout, stderr = ssh.exec_command("cd sipp-3.3; sudo ./sipp -sn uac_pcap " + self.hosts + " -i " + self.hostc + " -r 130 -rp 10s -bg > ~/sipp-cl.log 2>&1 &")
   	print stdout.read()
    	print stderr.read()
    def stop_server(self):
	ssh=get_ssh(self.hosts_ssh)
    	stdin, stdout, stderr = ssh.exec_command(self.killall)
    	self.server_process.terminate()
    def stop_client(self):
    	ssh=get_ssh(self.hostc_ssh)
    	stdin, stdout, stderr = ssh.exec_command(self.killall)
    	self.client_process.terminate()
