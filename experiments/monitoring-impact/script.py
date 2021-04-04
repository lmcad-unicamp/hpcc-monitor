import pyzabbix
import os
import numpy as np
# ==================================ACTIVE VIRTUAL ENVIRONMENT================
activate = "/home/theorangewill/Tools/clap/clap-env/bin/activate_this.py"
exec(open(activate, 'r').read(), dict(__file__=activate))
from clap.common.factory import PlatformFactory

# ================================ZABBIX======================================
home = os.path.dirname(os.path.realpath(__file__))
IPSERVER = (open(home+"/../../private/ip_server", "r")).read().strip('\n')
ZABBIX_USER = (open(home+"/../..//private/zabbix_user", "r")
               ).read().strip('\n')
ZABBIX_PASSWORD = (
    open(home+"/../..//private/zabbix_password", "r")).read().strip('\n')
zapi = pyzabbix.ZabbixAPI("http://"+str(IPSERVER)+"/zabbix/api_jsonrpc.php")
zapi.login(ZABBIX_USER, ZABBIX_PASSWORD)

def add_tag(id, tag, value):
    host = zapi.host.get(output=['hostid'], selectTags=['tag', 'value'], filter={'host': id})
    yep = False
    for t in host[0]['tags']:
        if t['tag'] == TAG_NAME:
            yep = True
    if not yep:
        host[0]['tags'].append({'tag': str(tag), 'value': str(value)})
    zapi.host.update(hostid=host[0]['hostid'], tags=host[0]['tags'])

# ============================================================================
NUM_THREADS = 8
DURATION = 5*60
APPLICATION = 'cg'
CLASS = 'D'
EXP = "monitoring-impact"
SCRIPT = "nas-script.sh"
RESULT_FILE = "/home/ubuntu/monitoring-impact.exp"
INFOS_FILE = "/home/ubuntu/monitoring-impact.infos"

TAG_NAME = 'experimento'
TAG_VALUE = EXP
# ============================================================================

node_module = PlatformFactory.get_module_interface().get_module('node')
group_module = PlatformFactory.get_module_interface().get_module('group')

# Run the without monitoring
for i in range(2,3):
    instance = (node_module.start_nodes({'r52xlarge': 1}))[0]

    node_module.execute_playbook(node_ids=[instance.node_id], 
                                    playbook_file=home+"/run-script.yml", 
                                    extra_args={'src': SCRIPT, 'args': str(NUM_THREADS)+' '
                                                                    +APPLICATION+' '
                                                                    +CLASS+' '
                                                                    +str(DURATION)})
    node_module.execute_playbook(node_ids=[instance.node_id],
                                    playbook_file=home+"/fetch.yml", 
                                    extra_args={'src': RESULT_FILE, 
                                                'dest': home+'/monitoring-impact.'+str(i+1)+'.nomonitoring.exp'})
    node_module.execute_playbook(node_ids=[instance.node_id], 
                                    playbook_file=home+"/fetch.yml", 
                                    extra_args={'src': INFOS_FILE, 
                                                'dest': home+'/monitoring-impact.'+str(i+1)+'.nomonitoring.infos'})
    node_module.stop_nodes([instance.node_id])

# Run with monitoring
for i in range(1,5):
    instance = (node_module.start_nodes({'r52xlarge': 1}))[0]
    group_module.add_group_to_node(node_ids=[instance.node_id], group="zabbix")
    add_tag(instance.instance_id, TAG_NAME, TAG_VALUE)

    node_module.execute_playbook(node_ids=[instance.node_id], 
                                    playbook_file=home+"/run-script.yml", 
                                    extra_args={'src': SCRIPT, 'args': str(NUM_THREADS)+' '
                                                                    +APPLICATION+' '
                                                                    +CLASS+' '
                                                                    +str(DURATION)})
    node_module.execute_playbook(node_ids=[instance.node_id],
                                    playbook_file=home+"/fetch.yml", 
                                    extra_args={'src': RESULT_FILE, 
                                                'dest': home+'/monitoring-impact.'+str(i+1)+'.monitoring.exp'})
    node_module.execute_playbook(node_ids=[instance.node_id], 
                                    playbook_file=home+"/fetch.yml", 
                                    extra_args={'src': INFOS_FILE, 
                                                'dest': home+'/monitoring-impact.'+str(i+1)+'.monitoring.infos'})
    node_module.stop_nodes([instance.node_id])

