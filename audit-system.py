import logging
import os
import zapi as z
import awsapi as aws
from zapi import NotFoudException
from sendemail import alert_email
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

ACCESS_ID = (open(home+"/private/aws_access_key", "r")).read().strip('\n')
SECRET_KEY = (open(home+"/private/aws_secret_access_key", "r")).read().strip('\n')
STOPPED_INSTANCES_FILE = home+"/files/stopped-instances.hosts"
NOTREGISTERED_INSTANCES_FILE = home+"/files/notregistered-instances.hosts"

stoppedInstancesFromFile = []
if os.path.isfile(STOPPED_INSTANCES_FILE):
    stoppedInstancesFromFile = filter(lambda x: x != '',(open(str(STOPPED_INSTANCES_FILE),"r")).read().split('\n'))
stoppedInstances = {}
for stopped in [ x.split(',') for x in stoppedInstancesFromFile]:
    stoppedInstances[stopped[0]] = datetime.strptime(stopped[1],'%Y-%m-%d %H:%M:%S')

notregisteredInstancesFromFile = []
if os.path.isfile(NOTREGISTERED_INSTANCES_FILE):
    notregisteredInstancesFromFile = filter(lambda x: x != '',(open(str(NOTREGISTERED_INSTANCES_FILE),"r")).read().split('\n'))

drivers = []
drivers.append(aws.getInstances('us-east-1'))
drivers.append(aws.getInstances('us-east-2'))

time6minutes = timedelta(minutes=6)
now = datetime.utcnow()
hostsFromProvider = []
stoppedHostsFromProvider = []
terminatedHostsFromProvider = []
users = z.getUsers()
userNotRegistered = []

f = open(str(STOPPED_INSTANCES_FILE),"w")
for driver in drivers:
    for node in driver:
        if node['owner'] in users:
            if now - node['launchtime'] > time6minutes:
                if node['zabbixignore']:
                    continue
                if node['state'] in ['stopped', 'stopping']:
                    stoppedHostsFromProvider.append(node['id'])
                    f.write(str(node['id'])+','+str(node['launchtime'])+'\n')
                elif node['state'] not in ['terminated', 'shutting-down']:
                    hostsFromProvider.append({'id':node['id'], 'owner':node['owner']})
        elif node['owner'] not in userNotRegistered:
            userNotRegistered.append(node['owner'])
f.close()


hostsFromZabbix = z.zapi.host.get(output = ['name'], filter={'status':'0'})
hostsFromZabbix = [x for x in hostsFromZabbix if not ("10084" == x.get('hostid'))]

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
    notregisteredInstances[notregistered[0]] = datetime.strptime(notregistered[1],'%Y-%m-%d %H:%M:%S')


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
                logger.info("[AUDIT] [NOT REGISTERED] SENDING AN EMAIL TO ADMINS AND " + host['owner'])
                #alert_email(emails,host['id'])
            except (NotFoudException,KeyError) as e:
                logger.error("[AUDIT] [NOT REGISTERED] COULD NOT SEND EMAIL")
                logger.error(e)
        else:
            newNotregisteredInstances.append(str(host['id'])+','+str(notregisteredInstances[host['id']]))

f = open(str(NOTREGISTERED_INSTANCES_FILE),"w")
for notregistered in newNotregisteredInstances:
    f.write(str(notregistered)+'\n')
f.close()
