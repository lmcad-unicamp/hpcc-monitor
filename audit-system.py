import logging
import os
import zapi as z
from zapi import NotFoudException
from sendemail import alert_email
from libcloud.compute.types import Provider
from libcloud.compute.providers import get_driver
from datetime import datetime,timedelta

home = os.path.dirname(os.path.realpath(__file__))

logger = logging.getLogger(__file__)
logger.setLevel(logging.INFO)
fh = logging.FileHandler(home+"/log/audit.log")
ch = logging.StreamHandler()
formatter = logging.Formatter('[%(asctime)s] - [%(levelname)5s] - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(ch)

ACCESS_ID = (open(home+"/private/aws_access_key", "r")).read()[:-1]
SECRET_KEY = (open(home+"/private/aws_secret_access_key", "r")).read()[:-1]
STOPPED_INSTANCES_FILE = home+"/files/stopped-instances.hosts"
NOTREGISTERED_INSTANCES_FILE = home+"/files/notregistered-instances.hosts"

cls = get_driver(Provider.EC2)
drivers = []
drivers.append(cls(ACCESS_ID, SECRET_KEY, region="us-east-2"))

stoppedInstancesFromFile = []
if os.path.isfile(STOPPED_INSTANCES_FILE):
    stoppedInstancesFromFile = filter(lambda x: x != '',(open(str(STOPPED_INSTANCES_FILE),"r")).read().split('\n'))
stoppedInstances = {}
for stopped in [ x.split(',') for x in stoppedInstancesFromFile]:
    stoppedInstances[stopped[0]] = datetime.strptime(stopped[1],'%Y-%m-%dT%H:%M:%S.%fZ')

notregisteredInstancesFromFile = []
if os.path.isfile(NOTREGISTERED_INSTANCES_FILE):
    notregisteredInstancesFromFile = filter(lambda x: x != '',(open(str(NOTREGISTERED_INSTANCES_FILE),"r")).read().split('\n'))

time2minutes = timedelta(minutes=2)
now = datetime.utcnow()
hostsFromProvider = []
stoppedHostsFromProvider = []
terminatedHostsFromProvider = []
f = open(str(STOPPED_INSTANCES_FILE),"w")
for driver in drivers:
    for node in driver.list_nodes():
            launchtime = datetime.strptime(node.extra['launch_time'],'%Y-%m-%dT%H:%M:%S.%fZ')
            if now - launchtime > time2minutes:
                if 'zabbixignore' in node.extra['tags'] and node.extra['tags']['zabbixignore'] in ['true', 'True']:
                    continue
                if node.extra['status'] not in ['terminated', 'shutting-down']:
                    try:
                        hostsFromProvider.append({'id':node.id, 'owner':node.extra['tags']['owner']})
                    except:
                        #TIRAR ISSO
                        hostsFromProvider.append({'id':node.id, 'owner':'william'})
                if node.extra['status'] in ['stopped', 'stopping']:
                    stoppedHostsFromProvider.append(node.id)
                    f.write(str(node.id)+','+str(node.extra['launch_time'])+'\n')
                #elif node.id in [x for x in stoppedInstances.keys()]:
                #    z.host_enable(hostid=host[node.id])
f.close()

hostsFromZabbix = z.zapi.host.get(output = ['name'], filter={'status':'0'})
try:
    hostsFromZabbix.remove({u'hostid': u'10084', u'name': u'Zabbix server'})
except:
    pass


##DISABLE TRIGGERS FROM STOPPED INSTANCES
for stoppedHost in stoppedHostsFromProvider[:]:
    if stoppedHost in [ x for x in stoppedInstances.keys()]:
        stoppedHostsFromProvider.remove(stoppedHost)
        del stoppedInstances[stoppedHost]
stoppedHostsFromProvider = z.zapi.host.get(hostids=z.getHostsIDs(stoppedHostsFromProvider), selectTriggers=['triggerid', 'description', 'status'])
stoppedInstancesFromFile = z.zapi.host.get(hostids=z.getHostsIDs([x for x in stoppedInstances.keys()]), selectTriggers=['triggerid', 'description', 'status'])


for stoppedHost in stoppedHostsFromProvider:
    triggers = []
    for trigger in stoppedHost['triggers']:
        z.zapi.trigger.update(triggerid=trigger['triggerid'], status = '1')
        triggers.append(trigger['triggerid'])
    logger.info("[AUDIT] HOST " + str(stoppedHost['host']) + " WAS STOPPED, SO I DISABLED THESE TRIGGERS: " + str(', '.join(triggers)))

for stoppedHost in stoppedInstancesFromFile:
    triggers = []
    for trigger in stoppedHost['triggers']:
        z.zapi.trigger.update(triggerid=trigger['triggerid'], status = '0')
        triggers.append(trigger['triggerid'])
    logger.info("[AUDIT] HOST " + str(stoppedHost['host']) + " WAS STARTED, SO I ENABLED THESE TRIGGERS: " + str(', '.join(triggers)))

##DETECT NEW HOSTS NOT REGISTERED
notregisteredInstances = {}
for notregistered in [ x.split(',') for x in notregisteredInstancesFromFile]:
    notregisteredInstances[notregistered[0]] = datetime.strptime(notregistered[1],'%Y-%m-%d %H:%M:%S.%f')


newNotregisteredInstances = []
time10minutes = timedelta(minutes=10)
now = datetime.utcnow()

for host in hostsFromProvider:
    if host['id'] not in [ x['name'] for x in hostsFromZabbix]:
        if host['id'] not in [ x for x in notregisteredInstances.keys()] or now - notregisteredInstances[host['id']] > time10minutes:
            newNotregisteredInstances.append(str(host['id'])+','+str(datetime.utcnow()))
            logger.info("[AUDIT] [NOT REGISTERED] Host ("+str(host['id'])+") has not been registered")
            try:
                useremail = z.getUserEmail(host['owner'],selectMedias=[])
                emails = z.getAdminsEmail()
                emails.append(useremail)
                logger.info("[AUDIT] [NOT REGISTERED] I AM SENDING AN EMAIL TO ADMINS AND " + host['owner'])
                alert_email(emails,host['id'])
            except (NotFoudException,KeyError) as e:
                logger.error("[AUDIT] [NOT REGISTERED] I COULD NOT SEND EMAIL")
                logger.error(e)
        else:
            newNotregisteredInstances.append(str(host['id'])+','+str(notregisteredInstances[host['id']]))

f = open(str(NOTREGISTERED_INSTANCES_FILE),"w")
for notregistered in newNotregisteredInstances:
    f.write(str(notregistered)+'\n')
f.close()
