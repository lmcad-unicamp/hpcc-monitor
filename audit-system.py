import zapi as z
import smtplib
from email.mime.text import MIMEText
from zapi import NotFoudException
from libcloud.compute.types import Provider
from libcloud.compute.providers import get_driver
from pprint import pprint

IPSERVER= (open("/home/william/Zabbix/private/ip-server", "r")).read()[:-1]
ZABBIX_USER= (open("/home/william/Zabbix/private/zabbix_user", "r")).read()[:-1]
ZABBIX_PASSWORD= (open("/home/william/Zabbix/private/zabbix_password", "r")).read()[:-1]
EMAIL_USER= (open("/home/william/Zabbix/private/email_user", "r")).read()[:-1]
EMAIL_PASSWORD= (open("/home/william/Zabbix/private/email_password", "r")).read()[:-1]
ACCESS_ID = (open("/home/william/.clap/private/access-key", "r")).read()[:-1]
SECRET_KEY = (open("/home/william/.clap/private/secret-access-key", "r")).read()[:-1]
STOPPED_INSTANCES_FILE = "files/stopped-instances.hosts"
cls = get_driver(Provider.EC2)
drivers = []
drivers.append(cls(ACCESS_ID, SECRET_KEY, region="us-east-2"))
s = smtplib.SMTP_SSL(host='smtp.gmail.com', port=465)
s.ehlo()
s.login(EMAIL_USER, EMAIL_PASSWORD)


def alert_email(emails, host):
    message = "WARNING: YOU HAVE A INSTANCE THAT IS NOT BEING MONITORED!\n\n"
    message = message + "Please, install the agent in your instance (" + host + ")"
    message = message + ", more info you can get here: lmcad.com/agentinstallation"
    msg = MIMEText(message)
    msg['Subject'] = "URGENT: there is a host unregistered"
    msg['From'] = EMAIL_USER
    msg['To'] = ", ".join(emails)
    s.sendmail(EMAIL_USER, emails, msg.as_string())

stoppedInstancesFromFile = filter(lambda x: x != '',(open(str(STOPPED_INSTANCES_FILE),"r")).read().split('\n'))

hostsFromProvider = []
stoppedHostsFromProvider = []
terminatedHostsFromProvider = []
for driver in drivers:
    for node in driver.list_nodes():
        #TIRAR ISSO
        if node.extra['tags']['owner'] == 'william':
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
    print("[AUDIT] HOST " + str(stoppedHost['host']) + " WAS STOPPED, SO I DISABLED THESE TRIGGERS: " + str(', '.join(triggers)))

for stoppedHost in stoppedInstancesFromFile:
    triggers = []
    for trigger in stoppedHost['triggers']:
        z.zapi.trigger.update(triggerid=trigger['triggerid'], status = '0')
        triggers.append(trigger['triggerid'])
    print("[AUDIT] HOST " + str(stoppedHost['host']) + " WAS STARTED, SO I ENABLED THESE TRIGGERS: " + str(', '.join(triggers)))

##DETECT NEW HOSTS NOT REGISTERED
for host in hostsFromProvider:
    if host['id'] not in [ x['name'] for x in hostsFromZabbix]:
        print("[AUDITOR] [NOT REGISTERED] Host ("+str(host['id'])+") has not been registered")
        try:
            useremail = z.getUserEmail(host['owner'],selectMedias=[])
            emails = z.getAdminsEmail()
            emails.append(useremail)
            print("[AUDITOR] [NOT REGISTERED] I AM SENDING AN EMAIL TO ADMINS AND " + host['owner'])
            alert_email(emails,host['id'])
        except (NotFoudException,KeyError) as e:
            print("[AUDITOR] [NOT REGISTERED] I COULD NOT SEND EMAIL")
            print(e)
s.close()
