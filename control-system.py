import logging
import os
import zapi as z
import boto3 as boto
import awsapi as aws
from sendemail import usernotfound_email
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

ACCESS_ID = (open(home+"/private/aws_access_key", "r")).read().strip('\n')
SECRET_KEY = (open(home+"/private/aws_secret_access_key", "r")).read().strip('\n')
NOTREGISTERED_USERS_FILE = home+"/files/notregistered-users.users"

drivers = []
drivers.append(aws.getInstances('us-east-1'))
drivers.append(aws.getInstances('us-east-2'))

users = z.getUsers()

hostsFromProvider = []
hostsFromProviderStopped = []
for driver in drivers:
    for node in driver:
        if node['owner'] in users:
            if node['zabbixignore']:
                continue
            if node['state'] not in ['terminated', 'shutting-down', 'stopped']:
                hostsFromProvider.append({'id':node['id'], 'owner':node['owner'], 'launchtime':node['launchtime']})
            elif node['state'] in ['stopped']:
                hostsFromProviderStopped.append({'id':node['id']})

hostsFromZabbix = z.zapi.host.get(output = ['name'], filter={'status':'0'})
hostsFromZabbix = [x for x in hostsFromZabbix if not ("10084" == x.get('hostid'))]

##DETECT TERMINATED INSTACES AND DISABLE HOSTS]
for host in hostsFromZabbix:
    if host['name'] in [x['id'] for x in hostsFromProviderStopped]:
        hostsFromZabbix.remove(host)
    elif host['name'] not in [x['id'] for x in hostsFromProvider]:
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
