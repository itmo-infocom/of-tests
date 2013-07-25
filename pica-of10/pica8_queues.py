#!/usr/bin/python

import subprocess

class OVSQueueAdapter:
    ovs_path = '/usr/bin/ovs-vsctl'
    debug = True

    def __init__(self,port_array,conn_str):
        self.ports = port_array
        self.conn_str = conn_str

    def custom_command(self,param_array,output_marker):
        p = subprocess.Popen([self.ovs_path, '--db=' + self.conn_str] + param_array, 
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out = p.stdout.readlines()
        err = p.stderr.readlines()
        print output_marker + " stdout: " + `out`
        print output_marker + " stderr: " + `err`
	if err:
	    print 'stderr not empty - terminating'
	    sys.exit(-1)
        return out

    def destroy_qos_queues(self):
        lines = self.custom_command(['list','QoS'],'list QoS')
        if len(lines) == 0:
            print 'No QoS was present'
            return

        uuid = lines[0].split(':')[1].strip()
        params_list = ['destroy', 'QoS', uuid]
        for port in self.ports:
            params_list.extend(['--', 'clear', 'Port', port, 'qos'])
        lines = self.custom_command(params_list,'destroy QoS')
        print 'QoS was destroyed'

        lines = self.custom_command(['list','Queue'],'list Queue')
        if len(lines) == 0:
            print 'No queues were present'
            return

        params_list = ['destroy', 'Queue']
        for line in lines:
            prefix = line.split(':')
            if prefix[0].strip() == '_uuid':
                params_list.append(prefix[1].strip())
        self.custom_command(params_list,'destroy Queue')
        print 'Queues were destroyed'

    def create_qos_queues(self,queue_params_dict):
        params_list = []
        for port in self.ports:
            params_list.extend(['--', 'set', 'Port', port, 'qos=@newqos'])
        params_list.extend(['--','--id=@newqos','create','QoS','type=linux-htb'])
        queues_string = 'queues='
        i = 0
        sublist = []
        for queue_key,queue_params in queue_params_dict.iteritems():
            queues_string += (queue_key + '=@q' + str(i) + ',')
            sublist.extend(['--', '--id=@q'+str(i), 'create', 'Queue'])
            for key,value in queue_params.iteritems():
                sublist.append('other-config:'+key+'='+str(value))
	    i += 1
        # removing last comma    
        queues_string = queues_string[:-1]  
        params_list.append(queues_string)
        params_list.extend(sublist)
        self.custom_command(params_list,'create QoS')
        print 'QoS and queues were created'

if __name__ == '__main__':
    adapter = OVSQueueAdapter(['ge-1/1/1','ge-1/1/11','ge-1/1/12'],'tcp:10.10.10.17:6633')
    adapter.destroy_qos_queues()
    adapter.create_qos_queues({'0':{'priority':1,
                                    'min-rate':0,
                                    'max-rate':10000000},
                            '1':{'priority':0,
                                 'min-rate':10000000,
                                 'max-rate':100000000}})

