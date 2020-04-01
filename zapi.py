import logging
import os
import pyzabbix
from awsapi import getpricing,gettype,getfamily

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class NotFoudException(Exception):
    pass

def getHostID(hostname):
    for host in zapi.host.get():
        if host['name'] == hostname:
            return str(host['hostid'])
    raise NotFoudException("[ZAPI] HOST DOES NOT EXIST: " + str(hostname))

def getHostsIDs(hostnames):
    hosts = []
    if not hostnames:
        return []
    for host in zapi.host.get():
        if host['name'] in hostnames:
            hosts.append(host['hostid'])
    if not hosts:
        raise NotFoudException("[ZAPI] HOST DOES NOT EXIST: " + str(hostnames))
    return hosts

def getHostname(hostid):
    for host in zapi.host.get():
        if host['hostid'] == hostid:
            return str(host['name'])
    raise NotFoudException("[ZAPI] HOST DOES NOT EXIST: " + str(hostname))

def getUserID(username):
    for user in zapi.user.get():
        if user['alias'] == username:
            return str(user['userid'])
    raise NotFoudException("[ZAPI] USER DOES NOT EXIST: " + str(username))

def getUserEmail(username, selectMedias=None):
    for user in zapi.user.get(selectMedias=['mediatypeid','sendto']):
        if user['alias'] == username:
            if user['medias']:
                flag = False
                for media in user['medias']:
                    if media['mediatypeid'] == '1':
                        flag = True
                        if media['sendto']:
                            return media['sendto'][0]
                        else:
                            raise NotFoudException("[ZAPI] USER DOES NOT HAVE AN EMAIL: " + str(username))
                if not flag:
                    raise NotFoudException("[ZAPI] USER DOES NOT HAVE AN EMAIL: " + str(username))
            else:
                raise NotFoudException("[ZAPI] USER DOES NOT HAVE MEDIA: " + str(username))
    raise NotFoudException("[ZAPI] USER DOES NOT EXIST: " + str(username))

def getAdminsEmail():
    emails = []
    for user in zapi.user.get(usrgrpids=['16'], selectMedias=['mediatypeid','sendto']):
        username = user['alias']
        if user['medias']:
            flag = False
            for media in user['medias']:
                if media['mediatypeid'] == '1':
                    flag = True
                    if media['sendto']:
                        emails.append(media['sendto'][0])
                    else:
                        logger.debug("[ZAPI] USER DOES NOT HAVE AN EMAIL: " + str(username))
            if not flag:
                logger.debug("[ZAPI] USER DOES NOT HAVE AN EMAIL: " + str(username))
        else:
            logger.debug("[ZAPI] USER DOES NOT HAVE MEDIA: " + str(username))
    if not emails:
        raise NotFoudException("[ZAPI] ADMINS DO NOT HAVE EMAILS")
    return emails

def getTemplateID(templatename):
    for template in zapi.template.get():
        if template['name'] == templatename:
            return str(template['templateid'])
    raise NotFoudException("[ZAPI] TEMPLATE DOES NOT EXIST: " + str(templatename))

def getHostGroupID(hostgroupname):
    for hostgroup in zapi.hostgroup.get():
        if hostgroup['name'] == hostgroupname:
            return str(hostgroup['groupid'])
    raise NotFoudException("[ZAPI] HOST GROUP DOES NOT EXIST: " + str(hostgroupname))

IPSERVER= (open(os.environ['HOME']+"/monitoring-system/private/ip_server", "r")).read()[:-1]
ZABBIX_USER= (open(os.environ['HOME']+"/monitoring-system/private/zabbix_user", "r")).read()[:-1]
ZABBIX_PASSWORD= (open(os.environ['HOME']+"/monitoring-system/private/zabbix_password", "r")).read()[:-1]


zapi = pyzabbix.ZabbixAPI("http://"+str(IPSERVER)+"/zabbix/api_jsonrpc.php")
zapi.login(ZABBIX_USER, ZABBIX_PASSWORD)

##DESABILITA OS HOSTS TERMINADOS
def host_disable(hostname=None, hostid=None):
    try:
        if hostname:
            hostid = getHostID(hostname)
        elif hostid:
            hostname = getHostname(hostid)
        else:
            logger.error("[ZAPI] I NEED A HOST ID OR NAME")
            return
        zapi.host.update(hostid=hostid, status="1")
        logger.info("[DISABLE] HOST "+str(hostname)+" HAS BEEN TERMINATED AND WAS DISABLED")
    except (pyzabbix.ZabbixAPIException,NotFoudException) as e:
        logger.error(e)

##ASSOCIA OS HOSTS AO USUARIO
def host_user_association(user=None, hostname=None, hostid=None):
    try:
        if hostname:
            hostid = getHostID(hostname)
        elif hostid:
            hostname = getHostname(hostid)
        else:
            logger.error("[ZAPI] I NEED A HOST ID OR NAME")
            return
        if not user:
            logger.error("[ZAPI] I NEED A USER")
            return

        groupOfUser = getHostGroupID(str(user)+"-hosts")
        groupsFromHost = zapi.hostgroup.get(hostids=hostid, output=["groupsid"])
    except NotFoudException as e:
        logger.error(e)
    else:
        if groupOfUser not in [x['groupid'] for x in groupsFromHost]:
            groupsFromHost.append({"groupid": str(groupOfUser)})
            try:
                zapi.host.update(hostid=hostid, groups=groupsFromHost)
                logger.info("[ASSOCIATE] HOST "+str(hostname)+" IS NOW ASSOCIATE WITH USER "+str(user))
            except (pyzabbix.ZabbixAPIException,NotFoudException) as e:
                logger.error(e)

##ARRUMAR O PRECO DA INSTANCIA
def host_update_price(hostname=None, hostid=None):
    if hostname:
        hostid = getHostID(hostname)
        macrosFromHost = zapi.host.get(hostids=hostid, selectMacros="extend", output=["macros"])
    elif hostid:
        macrosFromHost = zapi.host.get(hostids=hostid, selectMacros="extend", output=["macros"])
        hostname = getHostname(hostid)
    else:
        logger.error("[ZAPI] I NEED A HOST ID OR NAME")

    hostprice = getpricing(hostname)
    macros = []
    flag = False
    flagprice = False
    for macro in macrosFromHost[0]['macros']:
        if '{$PRICE}' in macro['macro']:
            flag = True
            flagprice = True
            value = macro['value']
            if float(value) != float(hostprice):
                flagprice = False
                macro['value'] = hostprice
                logger.info("[PRICING] PRICE OF "+str(hostname)+" UPDATED FROM "+str(value)+" TO "+str(hostprice))
        macros.append(macro)

    if not flag:
        macro = {'macro':'{$PRICE}', 'value':str(hostprice)}
        macros.append(macro)
        logger.info("[PRICING] PRICE OF "+str(hostname)+" ADDED COSTING "+str(hostprice))

    if not flagprice:
        try:
            zapi.host.update(hostid=getHostID(hostname), macros=macros)
        except NotFoudException as e:
            logger.error(e)

##ARRUMAR O TIPO DA INSTANCIA
def host_update_type(hostname=None, hostid=None):
    if hostname:
        hostid = getHostID(hostname)
        macrosFromHost = zapi.host.get(hostids=hostid, selectMacros="extend", output=["macros"])
    elif hostid:
        macrosFromHost = zapi.host.get(hostids=hostid, selectMacros="extend", output=["macros"])
        hostname = getHostname(hostid)
    else:
        logger.error("[ZAPI] I NEED A HOST ID OR NAME")

    hosttype = gettype(hostname)
    hostfamily = getfamily(hosttype)

    macros = []
    flag = False
    flagtype = False
    lastvalue = None
    for macro in macrosFromHost[0]['macros']:
        if '{$TYPE}' in macro['macro']:
            flag = True
            flagtype = True
            lastvalue = macro['value']
            if str(lastvalue) != str(hosttype):
                flagtype = False
                macro['value'] = hosttype
                logger.info("[TYPE] TYPE OF "+str(hostname)+" CHANGED FROM "+str(lastvalue)+" TO "+str(hosttype))
        macros.append(macro)

    if not flag:
        macro = {'macro':'{$TYPE}', 'value':str(hosttype)}
        macros.append(macro)
        logger.info("[TYPE] TYPE OF "+str(hostname)+" ADDED "+str(hosttype))

    if not flagtype:
        try:
            zapi.host.update(hostid=getHostID(hostname), macros=macros)
        except NotFoudException as e:
            logger.error(e)

    if lastvalue and not flagtype:
        lastfamily = getfamily(lastvalue)

        if lastfamily != hostfamily:
            try:
                templateOfFamily = getTemplateID('aws-'+str(hostfamily)+"-template")
                templateOfLastFamily = getTemplateID('aws-'+str(lastfamily)+"-template")
                templatesFromHost = zapi.template.get(hostids=hostid, output=["templateid"])

                templatesFromHost.remove({"templateid": str(templateOfLastFamily)})
                templatesFromHost.append({"templateid": str(templateOfFamily)})
                zapi.host.update(hostid=hostid, templates=templatesFromHost)
                logger.info("[TYPE] HOST "+str(hostname)+" IS NOW ASSOCIATE WITH TEMPLATE "+str(hostfamily))
            except (pyzabbix.ZabbixAPIException,NotFoudException) as e:
                logger.error(e)
