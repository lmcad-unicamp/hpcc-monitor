import os
import numpy as np
import scipy.stats
# ==================================ACTIVE VIRTUAL ENVIRONMENT================
activate = "/home/theorangewill/Tools/clap/clap-env/bin/activate_this.py"
exec(open(activate, 'r').read(), dict(__file__=activate))
from clap.common.factory import PlatformFactory
home = os.path.dirname(os.path.realpath(__file__))

# ============================================================================
node_module = PlatformFactory.get_module_interface().get_module('node')
group_module = PlatformFactory.get_module_interface().get_module('group')
for i in range(0,10):
    instance = (node_module.start_nodes({'t2micro': 1}))[0]
    group_module.add_group_to_node(node_ids=[instance.node_id], group="zabbix") 
    group_module.execute_group_action(node_ids=[instance.node_id], action="fetch", 
                                    group="zabbix",
                                    group_args={'src': "/home/ubuntu/*.exp", 
                                                'dest': home+"/install-time."+str(i+1)+".exp"})
    node_module.stop_nodes([instance.node_id])

# ============================================================================
data = []
for file in os.listdir(home):
    if file.endswith(".exp"):
        with open(home+'/'+file, 'r') as f: 
            data.append((int(f.readline())-int(f.readline()))*-1)
print(data)
print('mean:', np.mean(data))
print('median:', np.median(data))