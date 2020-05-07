import logging
import os
import zapi as z
import awsapi as aws
from zapi import NotFoudException
from sendemail import notregistered_email,availablevolume_email
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
AVAILABLE_VOLUMES_FILE = home+"/files/available-volumes.hosts"

stoppedInstancesFromFile = []
if os.path.isfile(STOPPED_INSTANCES_FILE):
    stoppedInstancesFromFile = (open(str(STOPPED_INSTANCES_FILE),"r")).read().strip('\n').split('\n')
stoppedInstances = {}
for stopped in [ x.split(",") for x in stoppedInstancesFromFile if x]:
    stoppedInstances[stopped[0]] = datetime.strptime(stopped[1],'%Y-%m-%d %H:%M:%S')

notregisteredInstancesFromFile = []
if os.path.isfile(NOTREGISTERED_INSTANCES_FILE):
    notregisteredInstancesFromFile = (open(str(NOTREGISTERED_INSTANCES_FILE),"r")).read().strip('\n').split('\n')
notregisteredInstances = {}
for notregistered in [ x.split(',') for x in notregisteredInstancesFromFile if x]:
    notregisteredInstances[notregistered[0]] = datetime.strptime(notregistered[1],'%Y-%m-%d %H:%M:%S')

availableVolumesFromFile = []
if os.path.isfile(AVAILABLE_VOLUMES_FILE):
    availableVolumesFromFile = (open(str(NOTREGISTERED_INSTANCES_FILE),"r")).read().strip('\n').split('\n')
availableVolumes = {}
for available in [ x.split(',') for x in availableVolumesFromFile if x]:
    availableVolumes[available[0]] = datetime.strptime(available[1],'%Y-%m-%d %H:%M:%S')

users = z.getUsers()
now = datetime.utcnow()
time6minutes = timedelta(minutes=6)
time10minutes = timedelta(minutes=10)

volumes = []
volumes.extend(aws.getVolumes('us-east-2'))

volumesFromProvider = []
volumesFromProviderAvailable = []
for volume in volumes:
    if volume['owner'] in users:
        if volume['zabbixignore']:
            continue
        if volume['state'] in ['in-use']:
            volumesFromProvider.append({'id':volume['id'], 'owner':volume['owner'], 'attachments':volume['attachments'], 'launchtime':volume['launchtime']})
        elif volume['state'] in ['available']:
            volumesFromProviderAvailable.append({'id':volume['id'], 'owner':volume['owner'], 'launchtime':volume['launchtime']})

drivers = []
drivers.extend(aws.getInstances('us-east-1'))
drivers.extend(aws.getInstances('us-east-2'))

hostsFromProvider = []
stoppedHostsFromProvider = []
terminatedHostsFromProvider = []
userNotRegistered = []

f = open(str(STOPPED_INSTANCES_FILE),"w")
for instance in instances:
    if instance['owner'] in users:
        if now - instance['launchtime'] > time6minutes:
            if instance['zabbixignore']:
                continue
            if instance['state'] in ['stopped', 'stopping']:
                stoppedHostsFromProvider.append(instance['id'])
                f.write(str(instance['id'])+','+str(instance['launchtime'])+'\n')
            elif instance['state'] not in ['terminated', 'shutting-down']:
                hostsFromProvider.append({'id':instance['id'], 'owner':instance['owner']})
    elif instance['owner'] not in userNotRegistered:
        userNotRegistered.append(instance['owner'])
f.close()


hostsFromZabbix = z.zapi.host.get(output = ['name'], filter={'status':'0'})
hostsFromZabbix = [x for x in hostsFromZabbix if not ("10084" == x.get('hostid'))]

##DISABLE TRIGGERS FROM STOPPED INSTANCES
for stoppedHost in stoppedHostsFromProvider[:]:
    if stoppedHost in [ x for x in list(stoppedInstances.keys())]:
        stoppedHostsFromProvider.remove(stoppedHost)
        del stoppedInstances[stoppedHost]
stoppedHostsFromProvider = z.zapi.host.get(hostids=z.getHostsIDs(stoppedHostsFromProvider), selectTriggers=['triggerid', 'description', 'status'])
stoppedInstancesFromFile = z.zapi.host.get(hostids=z.getHostsIDs([x for x in list(stoppedInstances.keys())]), selectTriggers=['triggerid', 'description', 'status'])


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
newNotregisteredInstances = []
for host in hostsFromProvider:
    if host['id'] not in [ x['name'] for x in hostsFromZabbix]:
        if host['id'] not in [ x for x in list(notregisteredInstances.keys())] or now - notregisteredInstances[host['id']] > time10minutes:
            newNotregisteredInstances.append(str(host['id'])+','+str(datetime.utcnow()))
            logger.info("[AUDIT] [NOT REGISTERED] Host ("+str(host['id'])+") has not been registered")
            try:
                useremail = z.getUserEmail(host['owner'],selectMedias=[])
                emails = z.getAdminsEmail()
                emails.append(useremail)
                logger.info("[AUDIT] [NOT REGISTERED] SENDING AN EMAIL TO ADMINS AND " + host['owner'])
                notregistered_email(emails,host['id'])
            except (NotFoudException,KeyError) as e:
                logger.error("[AUDIT] [NOT REGISTERED] COULD NOT SEND EMAIL TO ADMINS AND " + host['owner'])
                logger.error(e)
        else:
            newNotregisteredInstances.append(str(host['id'])+','+str(notregisteredInstances[host['id']]))

f = open(str(NOTREGISTERED_INSTANCES_FILE),"w")
for notregistered in newNotregisteredInstances:
    f.write(str(notregistered)+'\n')
f.close()


##DETECT AVAILABLE VOLUMES
nowAvailableVolumes = []
for volume in volumesFromProviderAvailable:
    if volume['id'] not in [ x for x in list(availableVolumes.keys())] or now - availableVolumes[volume['id']] > time10minutes:
        nowAvailableVolumes.append(str(volume['id'])+','+str(datetime.utcnow()))
        logger.info("[AUDIT] Volume ("+str(volume['id'])+") is available for a long time")
        try:
            useremail = z.getUserEmail(volume['owner'],selectMedias=[])
            emails = z.getAdminsEmail()
            emails.append(useremail)
            logger.info("[AUDIT] SENDING AN EMAIL TO ADMINS AND " + volume['owner'])
            availablevolume_email(emails,volume['id'])
        except (NotFoudException,KeyError) as e:
            logger.error("[AUDIT] COULD NOT SEND EMAIL TO ADMINS AND " + volume['owner'])
            logger.error(e)
    else:
        nowAvailableVolumes.append(str(volume['id'])+','+str(availableVolumes[volume['id']]))

f = open(str(AVAILABLE_VOLUMES_FILE),"w")
for available in nowAvailableVolumes:
    f.write(str(available)+'\n')
f.close()
