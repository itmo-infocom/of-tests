#!/usr/bin/python

import paramiko


def iperf_server(host,hosts):
    ssh=get_ssh(host)
    stdin, stdout, stderr = ssh.exec_command("iperf -s")
    print stderr.read()

def iperf_client(host, hosts, hostc):
    ssh=get_ssh(host)
    stdin, stdout, stderr = ssh.exec_command("iperf -t 9999 -c " + hosts)
    print stdout.read()
    print stderr.read()

def iperf_stop(host):
    ssh=get_ssh(host)
    stdin, stdout, stderr = ssh.exec_command("killall iperf")

def sip_server(host,hosts):
    ssh=get_ssh(host)
    stdin, stdout, stderr = ssh.exec_command("cd sipp-3.3; ./sipp -sn uas -i " + hosts + " -bg > ~/sipp-serv.log 2>&1 &")
    print stderr.read()

def sip_client(host, hosts, hostc):
    ssh=get_ssh(host)
    stdin, stdout, stderr = ssh.exec_command("cd sipp-3.3; sudo ./sipp -sn uac_pcap " + hosts + " -i " + hostc + " -r 130 -rp 10s -bg > ~/sipp-cl.log 2>&1 &")
    print stdout.read()
    print stderr.read()

def sip_stop(host):
    ssh=get_ssh(host)
    stdin, stdout, stderr = ssh.exec_command("sudo killall sipp")

def killall():
    print "Killing ofprotocol ofdatapath nox_core"
    os.system('killall ofprotocol ofdatapath nox_core 2> /dev/null')

def test_setup():
    print "Starting 'ofdatapath -v -i eth1,eth2 punix:/var/run/s1.sock > /tmp/s1-ofd.log 2>&1 &'"
    os.system('ofdatapath -v -i eth1,eth2 punix:/var/run/s1.sock > /tmp/s1-ofd.log 2>&1 &')
    print "Starting 'ofprotocol unix:/var/run/s1.sock tcp:127.0.0.1:6633 > /tmp/s1-ofp.log 2>&1 &'"
    os.system('ofprotocol unix:/var/run/s1.sock tcp:127.0.0.1:6633 > /tmp/s1-ofp.log 2>&1 &')
    print "Starting '/usr/local/bin/nox_core --libdir=/usr/local/lib -v -i ptcp:6633 switchqos > /tmp/nox.log 2>&1 &'"
    os.system('cd /usr/local/bin/; /usr/local/bin/nox_core --libdir=/usr/local/lib -v -i ptcp:6633 switchqos > /tmp/nox.log 2>&1 &')

    while not os.path.exists('/var/run/s1.sock'):
        time.sleep(1)

def get_ssh(host):
    ssh=paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username="openflow", password="openflow")
    return ssh

def io_test(host):
    ssh=get_ssh(host)
    stdin, stdout, stderr = ssh.exec_command("sudo /usr/local/bin/iscsi_test")

    #print stdout.read()
    print "Disk I/O perf: "
    #print stderr.read().splitlines()[1]
    print stderr.read()

def qos_setup(iscsi, traf):
    print "QoS: iSCSI=%d TRAF=%d" % (iscsi, traf)
    os.system('dpctl unix:/var/run/s1.sock queue-mod 1 1 %d > /tmp/s1-queue.log' % traf)
    os.system('dpctl unix:/var/run/s1.sock queue-mod 1 2 %d >> /tmp/s1-queue.log' % iscsi)
    os.system('dpctl unix:/var/run/s1.sock queue-mod 2 1 %d >> /tmp/s1-queue.log' % traf)
    os.system('dpctl unix:/var/run/s1.sock queue-mod 2 2 %d >> /tmp/s1-queue.log' % iscsi)
    os.system('dpctl unix:/var/run/s1.sock queue-mod 1 3 %d >> /tmp/s1-queue.log' % traf)
    os.system('dpctl unix:/var/run/s1.sock queue-mod 2 3 %d >> /tmp/s1-queue.log' % traf)

def single_qos_test(iscsi, traf, traf_client, traf_stop):
    # starting everything
    from multiprocessing import Process
    os.system('ifconfig eth1 up; ifconfig eth2 up')
    test_setup()
    if traf:
        c1 = Process(target=traf_client, args=('192.168.122.13','10.10.10.102','10.10.10.104'))
        c1.start()
    time.sleep(3)
    qos_setup(iscsi, traf)
    io_test('192.168.122.11')

    # stopping everything
    if traf:
        traf_stop('192.168.122.13')
        c1.join()
        c1.terminate()
    killall()
    os.system('ifconfig eth1 down; ifconfig eth2 down')

def traf_stop(host):
    iperf_stop(host)
    sip_stop(host)

def qos_tests(traf_client,traf_stop):
    single_qos_test(1000,0,traf_client,traf_stop)
    single_qos_test(1,1000,traf_client,traf_stop)  
    single_qos_test(1000,1,traf_client,traf_stop)
    single_qos_test(1000,1000,traf_client,traf_stop)
    single_qos_test(1,1,traf_client,traf_stop)

if __name__ == '__main__':
    import time
    import os.path
    import os
    import sys
    from multiprocessing import Process

    killall()
    paramiko.util.log_to_file('/tmp/paramiko.log')
    os.system('ifconfig eth1 down; ifconfig eth2 down')
    traf_stop('192.168.122.12')
    traf_stop('192.168.122.13')

    # IPERF test
    s1 = Process(target=iperf_server, args=('192.168.122.12','10.10.10.102'))
    s1.start()

    qos_tests(iperf_client, iperf_stop)

    iperf_stop('192.168.122.12')
    iperf_stop('192.168.122.13')
    s1.terminate()

    # SIP test
    s1 = Process(target=sip_server, args=('192.168.122.12','10.10.10.102'))
    s1.start()

    qos_tests(sip_client, sip_stop)

    sip_stop('192.168.122.12')
    sip_stop('192.168.122.13')
    s1.terminate()
