import logging
import os
import zapi as z
from libcloud.compute.types import Provider
from libcloud.compute.providers import get_driver
from datetime import datetime,timedelta

logger = logging.getLogger(__name__)
fh = logging.FileHandler(os.environ['HOME']+"/monitoring-system/log/control.log")
ch = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(ch)


ACCESS_ID = (open(os.environ['HOME']+"/monitoring-system/private/aws_access_key", "r")).read()[:-1]
SECRET_KEY = (open(os.environ['HOME']+"/monitoring-system/private/aws_secret_access_key", "r")).read()[:-1]

cls = get_driver(Provider.EC2)
drivers = []
drivers.append(cls(ACCESS_ID, SECRET_KEY, region="us-east-2"))

time = timedelta(minutes=2)
now = datetime.utcnow()

hostsFromProvider = []
for driver in drivers:
    for node in driver.list_nodes():
        #TIRAR ISSO
        if node.extra['tags']['owner'] == 'william':
            launchtime = datetime.strptime(node.extra['launch_time'],'%Y-%m-%dT%H:%M:%S.%fZ')
            if now - launchtime > time:
                if 'zabbixignore' in node.extra['tags'] and node.extra['tags']['zabbixignore'] == 'true':
                    continue
                if node.extra['status'] != 'terminated':
                    hostsFromProvider.append({'id':node.id, 'owner':node.extra['tags']['owner']})

##DETECT TERMINATED INSTACES AND DISABLE HOSTS
hostsFromZabbix = z.zapi.host.get(output = ['name'], filter={'status':'0'})
try:
    hostsFromZabbix.remove({u'hostid': u'10084', u'name': u'Zabbix server'})
    hostsFromZabbix.remove({u'hostid': u'10308', u'name': u'audit-system'})
except:
    pass

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

##ASSOCIATE USER AND HOST
for host in hostsFromZabbix:
    for hostProvider in hostsFromProvider:
        if host['name'] == hostProvider['id']:
            z.host_user_association(user=hostProvider['owner'],hostname=host['name'])


##DETECT NEW HOSTS (USER ASSOCIATION, ACTION CREATION)