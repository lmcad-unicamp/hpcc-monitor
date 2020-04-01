import logging
import os
import zapi as z
from zapi import NotFoudException
from sendemail import alert_email
from libcloud.compute.types import Provider
from libcloud.compute.providers import get_driver
from datetime import datetime,timedelta

logger = logging.getLogger(__name__)
fh = logging.FileHandler("log/audit.log")
ch = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(ch)

ACCESS_ID = (open(os.environ['HOME']+"/monitoring-system/private/aws_access_key", "r")).read()[:-1]
SECRET_KEY = (open(os.environ['HOME']+"/monitoring-system/private/aws_secret_access_key", "r")).read()[:-1]
STOPPED_INSTANCES_FILE = os.environ['HOME']+"/monitoring-system/files/stopped-instances.hosts"

cls = get_driver(Provider.EC2)
drivers = []
drivers.append(cls(ACCESS_ID, SECRET_KEY, region="us-east-2"))

stoppedInstancesFromFile = filter(lambda x: x != '',(open(str(STOPPED_INSTANCES_FILE),"r")).read().split('\n'))
time = timedelta(minutes=2)
now = datetime.utcnow()

hostsFromProvider = []
stoppedHostsFromProvider = []
terminatedHostsFromProvider = []
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
                if node.extra['status'] == 'stopped':
                    stoppedHostsFromProvider.append(node.id)

hostsFromZabbix = z.zapi.host.get(output = ['name'], filter={'status':'0'})
try:
    hostsFromZabbix.remove({u'hostid': u'10084', u'name': u'Zabbix server'})
except:
    pass

##DISABLE TRIGGERS FROM STOPPED INSTANCES
f = open(str(STOPPED_INSTANCES_FILE),"w")
for stoppedHost in stoppedHostsFromProvider:
    f.write(str(stoppedHost)+'\n')

for stoppedHost in stoppedHostsFromProvider[:]:
    if stoppedHost in stoppedInstancesFromFile[:]:
        stoppedHostsFromProvider.remove(stoppedHost)
        stoppedInstancesFromFile.remove(stoppedHost)

stoppedHostsFromProvider = z.zapi.host.get(hostids=z.getHostsIDs(stoppedHostsFromProvider), selectTriggers=['triggerid', 'description', 'status'])
stoppedInstancesFromFile = z.zapi.host.get(hostids=z.getHostsIDs(stoppedInstancesFromFile), selectTriggers=['triggerid', 'description', 'status'])

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
for host in hostsFromProvider:
    if host['id'] not in [ x['name'] for x in hostsFromZabbix]:
        logger.info("[AUDITOR] [NOT REGISTERED] Host ("+str(host['id'])+") has not been registered")
        try:
            useremail = z.getUserEmail(host['owner'],selectMedias=[])
            emails = z.getAdminsEmail()
            emails.append(useremail)
            logger.info("[AUDITOR] [NOT REGISTERED] I AM SENDING AN EMAIL TO ADMINS AND " + host['owner'])
            alert_email(emails,host['id'])
        except (NotFoudException,KeyError) as e:
            logger.error("[AUDITOR] [NOT REGISTERED] I COULD NOT SEND EMAIL")
            logger.error(e)
