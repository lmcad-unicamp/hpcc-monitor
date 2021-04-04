import pyzabbix
import os
import multiprocessing as mp
from joblib import Parallel, delayed
import time
import sys
# ==================================ACTIVE VIRTUAL ENVIRONMENT================
activate = "/home/theorangewill/Tools/clap/clap-env/bin/activate_this.py"
exec(open(activate, 'r').read(), dict(__file__=activate))
from clap.common.factory import PlatformFactory

# ================================ZABBIX======================================
home = os.path.dirname(os.path.realpath(__file__))
IPSERVER = (open(home+"/../../private/ip_server", "r")).read().strip('\n')
ZABBIX_USER = (open(home+"/../..//private/zabbix_user", "r")).read().strip('\n')
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
MINUTES = 5
if len(sys.argv) > 5:
    MINUTES = int(sys.argv[5])
NUM_THREADS = sys.argv[4]
DURATION = MINUTES*60 # 5 ou 15 ou 20 minutes
APPLICATION = sys.argv[2]
CLASS = sys.argv[3]
if sys.argv[4] == '1':
    EXP = "exp6-nas-" + APPLICATION + "-all-3"
elif sys.argv[4] == '16':
    EXP = "exp6-nas-" + APPLICATION + "16threads-3"
elif sys.argv[4] == '4':
    EXP = "exp6-nas-" + APPLICATION + "-1"
SCRIPT = "nas3-script.sh"
RESULT_FILE = "/home/ubuntu/*.exp"
INFOS_FILE = "/home/ubuntu/*.infos"
INSTANCE = sys.argv[1]

TAG_NAME = 'experimento'
TAG_VALUE = EXP
# ============================================================================
node_module = PlatformFactory.get_module_interface().get_module('node')
group_module = PlatformFactory.get_module_interface().get_module('group')
tag_module = PlatformFactory.get_module_interface().get_module('tag')

instance = (node_module.start_nodes({INSTANCE: 1}))[0]
tag_module.node_add_tag(node_ids=[instance.node_id], tags={TAG_NAME: TAG_VALUE})
group_module.add_group_to_node(node_ids=[instance.node_id], group="zabbix")
add_tag(instance.instance_id, TAG_NAME, TAG_VALUE)
    
group_module.execute_group_action(node_ids=[instance.node_id], group="zabbix",
                                action="run-script", 
                                group_args={'src': SCRIPT, 'args': instance.instance_type+' '+
                                                                str(NUM_THREADS)+' '
                                                                +APPLICATION+' '
                                                                +CLASS+' '
                                                                +str(DURATION)})
group_module.execute_group_action(node_ids=[instance.node_id], 
                                group="zabbix", action="fetch", 
                                group_args={'src': RESULT_FILE,'dest': home})
group_module.execute_group_action(node_ids=[instance.node_id], 
                                group="zabbix", action="fetch", 
                                group_args={'src': INFOS_FILE, 'dest': home})
node_module.stop_nodes([instance.node_id])
