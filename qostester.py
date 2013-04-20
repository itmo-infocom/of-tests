#!/usr/bin/python

import time
from trafgen import *

class QoSTester:
    sleep_timeout = 0
    def __init__(self,trafgen,iscsi_test_ip):
	self.trafgen = trafgen
	self.iscsi_test_ip = iscsi_test_ip
	self.test_cleanup()
	# server process is not killed after each test (unlike client)
	self.trafgen.run_server_process()
    def single_test(self,iscsi,traf):
	self.test_setup()
	if traf:
	    self.trafgen.run_client_process()
	    time.sleep(self.sleep_timeout)
	self.qos_setup(iscsi,traf)
	self.iscsi_test() # hangs here until iSCSI test is finished
	if traf:
	    self.trafgen.stop_client()
	self.test_cleanup()
    def test_setup(self):
	pass
    def qos_setup(self,iscsi,traf):
	pass
    def test_cleanup(self):
	pass
    def iscsi_test(self):
	pass
    def perform_tests(self):
	pass
    def finish(self):
	# should be called after end of all tests
	self.trafgen.stop_server()
