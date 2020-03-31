import zapi as z
from libcloud.compute.types import Provider
from libcloud.compute.providers import get_driver
from pprint import pprint

IPSERVER= (open("/home/william/Zabbix/private/ip-server", "r")).read()[:-1]
ZABBIX_USER= (open("/home/william/Zabbix/private/zabbix_user", "r")).read()[:-1]
ZABBIX_PASSWORD= (open("/home/william/Zabbix/private/zabbix_password", "r")).read()[:-1]
ACCESS_ID = (open("/home/william/.clap/private/access-key", "r")).read()[:-1]
SECRET_KEY = (open("/home/william/.clap/private/secret-access-key", "r")).read()[:-1]

cls = get_driver(Provider.EC2)
drivers = []
drivers.append(cls(ACCESS_ID, SECRET_KEY, region="us-east-2"))

hostsFromProvider = []
for driver in drivers:
    for node in driver.list_nodes():
        #TIRAR ISSO
        if node.extra['tags']['owner'] == 'william':
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
