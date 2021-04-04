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
IPSERVER = (open(home+"/../../../private/ip_server", "r")).read().strip('\n')
ZABBIX_USER = (open(home+"/../../..//private/zabbix_user", "r")).read().strip('\n')
ZABBIX_PASSWORD = (
    open(home+"/../../..//private/zabbix_password", "r")).read().strip('\n')
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
EXP = "exp7-nas-" + APPLICATION + "-4"
SCRIPT = "nas5-script.sh"
RESULT_FILE = "/home/ubuntu/*.exp"
INFOS_FILE = "/home/ubuntu/*.infos"
INSTANCES = {sys.argv[1]: 1}

START_NEW = True
GET_OLDERS = False
TAG_NAME = 'experimento'
TAG_VALUE = EXP
# ============================================================================
node_module = PlatformFactory.get_module_interface().get_module('node')
group_module = PlatformFactory.get_module_interface().get_module('group')
tag_module = PlatformFactory.get_module_interface().get_module('tag')
types = {}
instances = []
if GET_OLDERS or not START_NEW:
    instances.extend(node_module.list_nodes(tags={TAG_NAME: TAG_VALUE}))
if not instances:
    START_NEW = True
if START_NEW:
    new_instances = []
    for i in INSTANCES:
        new_instances.extend(node_module.start_nodes({i: INSTANCES[i]}))
    tag_module.node_add_tag(node_ids=[i.node_id for i in new_instances], tags={TAG_NAME: TAG_VALUE})
    instances.extend(new_instances)
for i in instances:
    if i.instance_type not in types:
        types[i.instance_type] = 0
    if 'n' not in i.extra:
        types[i.instance_type] = types[i.instance_type] + 1
        i.extra['n'] = types[i.instance_type]

    if 'zabbix' not in i.groups:
        group_module.add_group_to_node(node_ids=[i.node_id], group="zabbix")
    add_tag(i.instance_id, TAG_NAME, TAG_VALUE)
    
def run_script_parallel(instance):
    group_module_parallel = PlatformFactory.get_module_interface().get_module('group')
    node_module_parallel = PlatformFactory.get_module_interface().get_module('node')
    saida = 'eee'
    try:
        saida =     group_module_parallel.execute_group_action(node_ids=[instance.node_id], 
                                    group="zabbix",
                                    action="run-script", 
                                    group_args={'src': SCRIPT, 'args': instance.instance_type+' '+
                                                                        str(NUM_THREADS)+' '
                                                                        +APPLICATION+' '
                                                                        +CLASS+' '
                                                                        +str(DURATION)})
    except:
        print(saida)
    saida_exp = 'aaa'
    saida_info = 'bbb'
    try:
        saida_exp = group_module_parallel.execute_group_action(node_ids=[instance.node_id], 
                                    group="zabbix",
                                    action="fetch", 
                                    group_args={'src': RESULT_FILE, 
                                                'dest': home})
        saida_info = group_module_parallel.execute_group_action(node_ids=[instance.node_id], 
                                    group="zabbix",
                                    action="fetch", 
                                    group_args={'src': INFOS_FILE, 
                                                'dest': home})
        node_module_parallel.stop_nodes([instance.node_id])
    except:
        print(saida_exp)
        print(saida_info)
        node_module_parallel.resume_nodes([instance.node_id])

start = time.time()
if(len(instances) > 1):
    Parallel(n_jobs=len(instances))(
    delayed(run_script_parallel)(instances[i]) for i in range(len(instances)))
else:
    run_script_parallel(instances[0])
end = time.time()
print(end - start)
