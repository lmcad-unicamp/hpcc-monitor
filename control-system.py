import logging
import os
import zapi as z
from libcloud.compute.types import Provider
from libcloud.compute.providers import get_driver
from datetime import datetime,timedelta

home = os.path.dirname(os.path.realpath(__file__))

logger = logging.getLogger(str(__file__))
logger.setLevel(logging.INFO)
fh = logging.FileHandler(home+"/log/control.log")
ch = logging.StreamHandler()
formatter = logging.Formatter('[%(asctime)s] - [%(levelname)5s] - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(ch)

ACCESS_ID = (open(home+"/private/aws_access_key", "r")).read()[:-1]
SECRET_KEY = (open(home+"/private/aws_secret_access_key", "r")).read()[:-1]
STOPPED_INSTANCES_FILE = home+"/files/stopped-instances.hosts"

stoppedInstancesFromFile = []
if os.path.isfile(STOPPED_INSTANCES_FILE):
    stoppedInstancesFromFile = filter(lambda x: x != '',(open(str(STOPPED_INSTANCES_FILE),"r")).read().split('\n'))
stoppedInstances = {}
for stopped in [ x.split(',') for x in stoppedInstancesFromFile]:
    stoppedInstances[stopped[0]] = datetime.strptime(stopped[1],'%Y-%m-%dT%H:%M:%S.%fZ')


cls = get_driver(Provider.EC2)
drivers = []
drivers.append(cls(ACCESS_ID, SECRET_KEY, region="us-east-2"))


hostsFromProvider = []
for driver in drivers:
    for node in driver.list_nodes():
            if 'zabbixignore' in node.extra['tags'] and node.extra['tags']['zabbixignore'] in ['true','True']:
                continue
            if node.extra['status'] not in ['terminated', 'shutting-down']:
                try:
                    hostsFromProvider.append({'id':node.id, 'owner':node.extra['tags']['owner'], 'launchtime':datetime.strptime(node.extra['launch_time'],'%Y-%m-%dT%H:%M:%S.%fZ')})
                except:
                    #TIRAR ISSO
                    hostsFromProvider.append({'id':node.id, 'owner':'william', 'launchtime':datetime.strptime(node.extra['launch_time'],'%Y-%m-%dT%H:%M:%S.%fZ')})


hostsFromZabbix = z.zapi.host.get(output = ['name'], filter={'status':'0'})
try:
    hostsFromZabbix.remove({u'hostid': u'10084', u'name': u'Zabbix server'})
except:
    pass

##DETECT TERMINATED INSTACES AND DISABLE HOSTS
for host in hostsFromZabbix:
    if host['name'] not in [ x['id'] for x in hostsFromProvider]:
        z.host_disable(hostid=host['hostid'])
        hostsFromZabbix.remove(host)

##DETECT CHANGED INSTANCE TYPE
for host in hostsFromZabbix:
    z.host_update_type(hostid=host['hostid'])

##DETECT CHANGED PRICES
for host in hostsFromZabbix:
    z.host_update_price(hostid=host['hostid'])

##UPDATE uptime
now = datetime.utcnow()
for host in hostsFromZabbix:
    launchtime = [ x['launchtime'] for x in hostsFromProvider if str(x['id']) == str(host['name']) ][0]
    uptime = str(int((now - launchtime).total_seconds()))
    z.host_update_uptime(hostid=host['hostid'],uptime=uptime)


##ASSOCIATE USER AND HOST
for host in hostsFromZabbix:
    for hostProvider in hostsFromProvider:
        if host['name'] == hostProvider['id']:
            z.host_user_association(user=hostProvider['owner'],hostname=host['name'])
