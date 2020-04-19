import logging
import os
import zapi as z
from sendemail import usernotfound_email
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
NOTREGISTERED_USERS_FILE = home+"/files/notregistered-users.hosts"

stoppedInstancesFromFile = []
if os.path.isfile(STOPPED_INSTANCES_FILE):
    stoppedInstancesFromFile = filter(lambda x: x != '',(open(str(STOPPED_INSTANCES_FILE),"r")).read().split('\n'))
stoppedInstances = {}
for stopped in [ x.split(',') for x in stoppedInstancesFromFile]:
    stoppedInstances[stopped[0]] = datetime.strptime(stopped[1],'%Y-%m-%dT%H:%M:%S.%fZ')


cls = get_driver(Provider.EC2)
drivers = []
drivers.append(cls(ACCESS_ID, SECRET_KEY, region="us-east-2"))

users = z.getUsers()
hostsFromProvider = []
for driver in drivers:
    for node in driver.list_nodes():
        owner = node.extra['tags']['owner']
        if owner in users:
            if 'zabbixignore' in node.extra['tags'] and node.extra['tags']['zabbixignore'] in ['true','True']:
                continue
            if node.extra['status'] not in ['terminated', 'shutting-down']:
                hostsFromProvider.append({'id':node.id, 'owner':owner, 'launchtime':datetime.strptime(node.extra['launch_time'],'%Y-%m-%dT%H:%M:%S.%fZ')})

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

##UPDATE uptime
#now = datetime.utcnow()
#for host in hostsFromZabbix:
#    launchtime = [ x['launchtime'] for x in hostsFromProvider if str(x['id']) == str(host['name']) ][0]
#    uptime = str(int((now - launchtime).total_seconds()))
#    z.host_update_uptime(hostid=host['hostid'],uptime=uptime)


##ASSOCIATE USER AND HOST
for host in hostsFromZabbix:
    for hostProvider in hostsFromProvider:
        if host['name'] == hostProvider['id']:
            user = hostProvider['owner']
            try:
                z.getUserID(user)
            except z.NotFoudException as e:
                notregisteredUsersFromFile = []
                if os.path.isfile(NOTREGISTERED_USERS_FILE):
                    notregisteredUsersFromFile = filter(lambda x: x != '',(open(str(NOTREGISTERED_USERS_FILE),"r")).read().split('\n'))
                notregisteredUsers = {}
                for notregistered in [ x.split(',') for x in notregisteredUsersFromFile]:
                    notregisteredUsers[notregistered[0]] = datetime.strptime(notregistered[1],'%Y-%m-%d %H:%M:%S.%f')

                newNotregisteredUsers = []
                time30minutes = timedelta(minutes=30)
                now = datetime.utcnow()

                if user not in [ x for x in notregisteredUsers.keys()] or now - notregisteredUsers[user] > time30minutes:
                    newNotregisteredUsers.append(str(user)+','+str(datetime.utcnow()))
                    try:
                        logger.info("[CONTROL] [NOT REGISTERED] SENDING AN EMAIL TO ADMINS")
                        usernotfound_email(z.getAdminsEmail(),user)
                    except (z.NotFoudException,KeyError) as f:
                        logger.error("[CONTROL] [NOT REGISTERED] COULD NOT SEND EMAIL")
                        logger.error(f)
                else:
                    newNotregisteredUsers.append(str(user)+','+str(notregisteredUsers[user]))

                f = open(str(NOTREGISTERED_USERS_FILE),"w")
                for notregistered in newNotregisteredUsers:
                    f.write(str(notregistered)+'\n')
                f.close()
            else:
                z.host_user_association(user=user,hostname=host['name'])


##DETECT CHANGED INSTANCE TYPE
for host in hostsFromZabbix:
    z.host_update_type(hostid=host['hostid'])

##DETECT CHANGED PRICES
for host in hostsFromZabbix:
    z.host_update_price(hostid=host['hostid'])
