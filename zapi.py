import logging
import os
import re
import inspect
import pyzabbix
import pytz
from pprint import pprint
from datetime import datetime

home = os.path.dirname(os.path.realpath(__file__))
logger = logging.getLogger(str(inspect.getouterframes(inspect.currentframe()
                                                      )[-1].filename))

NOW = int(datetime.timestamp(datetime.utcnow().astimezone(pytz.utc)))
IPSERVER = (open(home+"/private/ip_server", "r")).read().strip('\n')
ZABBIX_USER = (open(home+"/private/zabbix_user", "r")).read().strip('\n')
ZABBIX_PASSWORD = (open(home+"/private/zabbix_password", "r")
                   ).read().strip('\n')

zapi = pyzabbix.ZabbixAPI("http://"+str(IPSERVER)+"/zabbix/api_jsonrpc.php")
zapi.login(ZABBIX_USER, ZABBIX_PASSWORD)


class NotFoudException(Exception):
    pass


# This function convert time to hour
def convert_to_hour(delay):
    number = re.findall(r'(\d+)', delay)
    unit = re.findall(r'(\D+)', delay)

    if unit[0] == 's':
        return (float(number[0]) * 1.0 / 3600.0)
    elif unit[0] == 'm':
        return (float(number[0]) * 1.0 / 60.0)
    else:
        return number[0]


# This function convert value type of this value
def convert_value_type(value, valuetype):
    if valuetype == '0':
        return float(value)
    elif valuetype in ['1', '2', '4']:
        return str(value)
    elif valuetype == '3':
        return int(value)


# Zabbix sender, send a value to a item
def send_item(host, item, value):
    if type(value) is dict:
        value = str(value)
    if type(value) is str:
        value = '"{}"'.format(value)
    print("zabbix_sender -z " + str(IPSERVER)
              + " -s " + '"{}"'.format(host)
              + " -k " + item
              + " -o " + str(value))
    os.system("zabbix_sender -z " + str(IPSERVER)
              + " -s " + '"{}"'.format(host)
              + " -k " + item
              + " -o " + str(value))


# Get the id of a host
def get_hostID(hostname):
    host = zapi.host.get(output=['hostid'], filter={'host': hostname})
    if host:
        return host[0]['hostid']
    else:
        raise NotFoudException("Host does not exist: " + hostname)


# Get the name of a host
def get_hostname(hostid):
    host = zapi.host.get(hostids=[hostid], output=['name'])
    if host:
        return host[0]['name']
    else:
        raise NotFoudException("Host does not exist: " + hostid)


# Get the id of an user
def get_userID(username):
    user = zapi.user.get(output=['userid'], filter={'alias': username})
    if user:
        return user[0]['userid']
    else:
        raise NotFoudException("User does not exist: " + username)


# Get the id of a template
def get_templateID(templatename):
    template = zapi.template.get(output=['templateid'],
                                 filter={'name': templatename})
    if template:
        return template[0]['templateid']
    else:
        raise NotFoudException("Template does not exist: " + templatename)


# Get the id of a hostgroup
def get_hostgroupID(hostgroupname):
    hostgroup = zapi.hostgroup.get(output=['groupid'],
                                   filter={'name': hostgroupname})
    if hostgroup:
        return hostgroup[0]['groupid']
    else:
        raise NotFoudException("Hostgroup does not exist: " + hostgroupname)


# Get all users from Zabbix Server
def get_users():
    users = []
    for user in zapi.user.get():
        users.append(user['alias'])
    return users


# Get email of a user
def get_user_email(username):
    try:
        user = zapi.user.get(userids=get_userID(username),
                             output=['userid'],
                             selectMedias=['mediatypeid', 'sendto'])
    except (pyzabbix.ZabbixAPIException, NotFoudException) as e:
        logger.error("[ZAPI] [get_user_email] Could not get email of user "
                     + username + ": " + str(e))
    else:
        for media in user[0]['medias']:
            if media['mediatypeid'] == '1':
                if media['sendto']:
                    return media['sendto'][0]
        raise NotFoudException("User does not have an email: "
                               + str(username))


# Get email of admins
def get_admins_email():
    try:
        admins = zapi.user.get(usrgrpids=['16'],
                               output=['userid', 'alias'],
                               selectMedias=['mediatypeid', 'sendto'])
    except pyzabbix.ZabbixAPIException as e:
        logger.error("[ZAPI] [get_admins_email] Could not get email of admins:"
                     + " " + str(e))
    else:
        emails = []
        for user in admins:
            flag = False
            username = user['alias']
            for media in user['medias']:
                if media['mediatypeid'] == '1':
                    if media['sendto']:
                        flag = True
                        emails.append(media['sendto'][0])
                        break
            if not flag:
                logger.error("[ZAPI] User does not have an email: "
                             + str(username))
        return emails


# Disable triggers from a host
def host_triggers_disable(host):
    triggers = [x for x in host['triggers']]
    try:
        for t in triggers:
            zapi.trigger.update(triggerid=t, status=1)
    except pyzabbix.ZabbixAPIException as e:
        logger.error("[ZAPI] [host_triggers_disable] Could not disable "
                     + "triggers " + ", ".join(triggers) + " of host " + host['id']
                     + ": " + str(e))
    else:
        logger.info("[ZAPI] [host_triggers_disable] Triggers "
                    + ", ".join(triggers) + " of host " + host['id']
                    + " were disabled")


# Disable triggers from a host
def host_triggers_enable(host):
    triggers = [x for x in host['triggers']]
    try:
        for t in triggers:
            zapi.trigger.update(triggerid=t, status=0)
    except pyzabbix.ZabbixAPIException as e:
        logger.error("[ZAPI] [host_triggers_enable] Could not enable trigger "
                     + ", ".join(triggers) + " of host " + host['id']
                     + ": " + str(e))
    else:
        logger.info("[ZAPI] [host_triggers_enable] Trigger "
                    + ", ".join(triggers) + " of host " + host['id']
                    + " were enabled")


# Disable a host from monitoring
def host_disable(host):
    try:
        zapi.host.update(hostid=host['id_zabbix'], status="1")
    except pyzabbix.ZabbixAPIException as e:
        logger.error("[ZAPI] [host_disable] Could not disable host "
                     + host['id'] + ": " + str(e))
    else:
        logger.info("[ZAPI] [host_disable] Host " + host['id']
                    + " has been terminated and was disabled")


# Enable a host from monitoring
def host_enable(host):
    try:
        zapi.host.update(hostid=host['id_zabbix'], status="0")
    except pyzabbix.ZabbixAPIException as e:
        logger.error("[ZAPI] [host_enable] Could not enable host "
                     + host['id'] + ": " + str(e))
    else:
        logger.info("[ZAPI] [host_enable] Host " + host['id']
                    + " has been restarted and was enabled")


# Register a host on Zabbix server
def register_volume(volume):
    pprint(volume)
    volume['launchtime'] = volume['launchtime'].strftime(
                                                        "%Y-%m-%d %H:%M:%S %z")
    if 'attachment' in volume and volume['attachment']:
        volume['attachment']['time'] = volume['attachment']['time'].strftime(
                                                        "%Y-%m-%d %H:%M:%S %z")
    if 'deattachment' in volume and volume['deattachment']:
        volume['deattachment'] = volume['deattachment'].strftime(
                                                        "%Y-%m-%d %H:%M:%S %z")
    pprint(volume)
    send_item('AWS Volumes', 'volumes.get', volume)
    logger.info("[ZAPI] [register_volume] Volume registered: " + volume['id'])


# Get hosts from Zabbix Server
def get_hosts(resource, output=None, filter=None, macros=None, triggers=None,
              templates=None, groups=None, items=None,
              user=False, provider=False, region=False, service=False,
              family=False, type=False, launchtime=False, filesystems=False):
    if not macros and (user or provider or region or service
                       or family or type or launchtime):
        macros = ['macro', 'value']
    if not items and filesystems:
        items = ['itemid', 'key_', 'value_type']
    try:
        hostsFromZabbix = zapi.host.get(output=output,
                                        selectTags=['tag', 'value'],
                                        filter=filter,
                                        selectMacros=macros,
                                        selectTriggers=triggers,
                                        selectParentTemplates=templates,
                                        selectGroups=groups,
                                        selectItems=items,
                                        groupids=get_hostgroupID(
                                                        'resource-'+resource))
    except pyzabbix.ZabbixAPIException as e:
        logger.error("[ZAPI] [get_hosts] Could not get hosts from server: "
                     + str(e))
    else:
        hosts = {}
        for host in hostsFromZabbix:
            # Eliminate ZabbixServer
            if host['tags']:
                for t in host['tags']:
                    if t == 'ignore' and host['tags'][t] in ['true', 'True']:
                        continue
            # Create a dictionary of macros for better handling
            if 'macros' in host:
                host['macros_zabbix'] = host['macros']
                host['macros'] = ({item['macro']: item['value']
                                   for item in host['macros']})
                # Get user
                if '{$USER}' in host['macros']:
                    host['user'] = host['macros']['{$USER}']
                else:
                    host['user'] = None
                # Get provider
                if '{$PROVIDER}' in host['macros']:
                    host['provider'] = host['macros']['{$PROVIDER}']
                else:
                    host['provider'] = None
                # Get region
                if '{$REGION}' in host['macros']:
                    host['region'] = host['macros']['{$REGION}']
                else:
                    host['region'] = None
                # Get type
                if '{$TYPE}' in host['macros']:
                    host['type'] = host['macros']['{$TYPE}']
                else:
                    host['type'] = None
                # Get family
                if '{$FAMILY}' in host['macros']:
                    host['family'] = host['macros']['{$FAMILY}']
                else:
                    host['family'] = None
                # Get service
                if '{$SERVICE}' in host['macros']:
                    host['service'] = host['macros']['{$SERVICE}']
                    host['service_id'] = host['macros']['{$SERVICE_ID}']
                else:
                    host['service'] = None
                    host['service_id'] = None
                # Get price
                if '{$PRICE}' in host['macros']:
                    host['price'] = host['macros']['{$PRICE}']
                else:
                    host['price'] = None
                # Get launchtime
                if '{$LAUNCHTIME}' in host['macros']:
                    host['launchtime'] = datetime.strptime(
                                            host['macros']['{$LAUNCHTIME}'],
                                            '%Y-%m-%d %H:%M:%S %z')
                else:
                    host['launchtime'] = None

            # Change the key of some attributes
            if 'parentTemplates' in host:
                host['templates_zabbix'] = host['parentTemplates']
                host['templates'] = ({item['name']: item
                                      for item in host['parentTemplates']})
                del host['parentTemplates']

            if 'triggers' in host:
                host['triggers_zabbix'] = host['triggers']
                host['triggers'] = ({item['triggerid']: item
                                     for item in host['triggers']})

            if 'groups' in host:
                host['groups_zabbix'] = host['groups']
                host['groups'] = ({item['name']: item
                                   for item in host['groups']})

            if 'items' in host:
                host['items_zabbix'] = host['items']
                host['items'] = ({item['key_']: item
                                   for item in host['items']})

            host['filesystems'] = []
            host['filesystems_all'] = []
            host['devices_without_filesystems'] = []
            host['filesystems_without_devices'] = []
            host['devices_filesystems'] = []
            # Get the filesystems
            if filesystems:
                for item in host['items']:
                    if item.find('vfs.fs.usage.free') != -1:
                        host['filesystems_all'].extend(re.findall(r'\[(.*)\]',
                                                       item))
                        history_price = get_history(host=host, since=0,
                                                    till=NOW, itemkey=item)
                        if (not history_price
                           or history_price[-1]['value'] != -1):
                            host['filesystems'].extend(re.findall(r'\[(.*)\]',
                                                       item))

            if 'name' in host:
                host['id'] = host['name']
                del host['name']

            host['id_zabbix'] = host['hostid']
            del host['hostid']

            hosts[host['id']] = host
        return hosts


# Associate the host with its user
def host_user_association(host):
    macros = host['macros']
    groupName = 'user-' + host['user'] + '-hosts'

    # If the USER macro is not present, it is added
    if '{$USER}' not in macros:
        host['macros_zabbix'].append({'macro': '{$USER}',
                                      'value': str(host['user'])})
        host['macros']['{$USER}'] = host['user']
        try:
            zapi.host.update(hostid=host['id_zabbix'],
                             macros=host['macros_zabbix'])
        except pyzabbix.ZabbixAPIException as e:
            logger.error("[ZAPI] [host_user_association] Could not add "
                         + "user " + host['user'] + " to the host "
                         + host['id'] + ": " + str(e))
        else:
            logger.info("[ZAPI] [host_user_association] The user of host "
                        + host['id'] + " added: " + host['user'])

    # If the group of the user, it is added
    if groupName not in host['groups']:
        try:
            groupID = get_hostgroupID(groupName)
        except NotFoudException as e:
            logger.error("[ZAPI] [host_user_association] Could not find "
                         + "grouphost for user " + host['user']
                         + ": " + str(e))
        else:
            host['groups_zabbix'].append({'groupid': groupID,
                                          'name': groupName})
            host['groups'][groupName] = {'groupid': groupID,
                                         'name': groupName}
            try:
                zapi.host.update(hostid=host['id_zabbix'],
                                 groups=host['groups_zabbix'])
            except pyzabbix.ZabbixAPIException as f:
                logger.error("[ZAPI] [host_user_association] Could not update "
                             + "host " + host['id'] + ": " + str(f))
            else:
                logger.info("[ZAPI] [host_user_association] The host "
                            + host['id'] + " is now associate with grouphost "
                            + groupName)


# Associate the host with its region
def host_region_association(host):
    macros = host['macros']

    # If the REGION macro is not present, if not it is added
    if '{$REGION}' not in macros:
        host['macros_zabbix'].append({'macro': '{$REGION}',
                                      'value': str(host['region'])})
        host['macros']['{$REGION}'] = host['region']
        try:
            zapi.host.update(hostid=host['id_zabbix'],
                             macros=host['macros_zabbix'])
        except pyzabbix.ZabbixAPIException as e:
            logger.error("[ZAPI] [host_region_association] Could not add "
                         + "region to the host " + host['id'] + ": " + str(e))
        else:
            logger.info("[ZAPI] [host_region_association] The region of host "
                        + host['id'] + " added: " + host['region'])


# Associate the host with its provider
def host_provider_association(host):
    macros = host['macros']

    # If the PROVIDER macro is not present, if not it is added
    if '{$PROVIDER}' not in macros:
        host['macros_zabbix'].append({'macro': '{$PROVIDER}',
                                      'value': str(host['provider'])})
        host['macros']['{$PROVIDER}'] = host['provider']
        try:
            zapi.host.update(hostid=host['id_zabbix'],
                             macros=host['macros_zabbix'])
        except pyzabbix.ZabbixAPIException as e:
            logger.error("[ZAPI] [host_provider_association] Could not add "
                         + "provider to the host " + host['id']
                         + ": " + str(e))
        else:
            logger.info("[ZAPI] [host_provider_association] The provider of "
                        + "host " + host['id'] + " added: " + host['provider'])


# Associate the host with its os
def host_os_association(host):
    macros = host['macros']

    # If the OS macro is not present, if not it is added
    if '{$OS}' not in macros:
        host['macros_zabbix'].append({'macro': '{$OS}',
                                      'value': str(host['os'])})
        host['macros']['{$OS}'] = host['os']
        try:
            zapi.host.update(hostid=host['id_zabbix'],
                             macros=host['macros_zabbix'])
        except pyzabbix.ZabbixAPIException as e:
            logger.error("[ZAPI] [host_os_association] Could not add "
                         + "os to the host " + host['id']
                         + ": " + str(e))
        else:
            logger.info("[ZAPI] [host_os_association] The os of "
                        + "host " + host['id'] + " added: " + host['os'])


# Associate the host with its service (ondemand, spot, reservation, dedicated)
def host_service_association(host):
    macros = host['macros']

    # If the SERVICE macro is not present, if not it is added
    if '{$SERVICE}' not in macros:
        host['macros_zabbix'].append({'macro': '{$SERVICE}',
                                      'value': str(host['service'])})
        host['macros_zabbix'].append({'macro': '{$SERVICE_ID}',
                                      'value': str(host['service_id'])})
        host['macros']['{$SERVICE}'] = host['service']
        host['macros']['{$SERVICE_ID}'] = host['service_id']
        try:
            zapi.host.update(hostid=host['id_zabbix'],
                             macros=host['macros_zabbix'])
        except pyzabbix.ZabbixAPIException as e:
            logger.error("[ZAPI] [host_service_association] Could not add "
                         + "service to the host " + host['id']
                         + ": " + str(e))
        else:
            logger.info("[ZAPI] [host_service_association] The service of "
                        + "host " + host['id'] + " added: " + host['service'])


# Associate the host with its lunchtime
def host_launchtime_association(host):
    macros = host['macros']
    print(host)
    # If the LAUNCHTIME macro is not present, if not it is added
    if '{$LAUNCHTIME}' not in macros:
        launchtime_string = host['launchtime'].strftime("%Y-%m-%d %H:%M:%S %z")
        host['macros_zabbix'].append({'macro': '{$LAUNCHTIME}',
                                      'value': launchtime_string})
        host['macros']['{$LAUNCHTIME}'] = launchtime_string
        try:
            zapi.host.update(hostid=host['id_zabbix'],
                             macros=host['macros_zabbix'])
        except pyzabbix.ZabbixAPIException as e:
            logger.error("[ZAPI] [host_launchtime_association] Could not add "
                         + "launchtime to the host " + host['id']
                         + ": " + str(e))
        else:
            logger.info("[ZAPI] [host_launchtime_association] The launchtime "
                        + "of host " + host['id'] + " added: "
                        + launchtime_string)


# Update the price of a host
def host_update_instance_price(host):
    macros = host['macros']
    changed = False
    # If there is a price
    if host['price']:
        # If the PRICE macro is present
        if '{$PRICE}' in macros:
            # Check its consistency, if it is different we update the macro
            if float(macros['{$PRICE}']) != round(host['price'], 6):
                lastprice = macros['{$PRICE}']
                for m in host['macros_zabbix']:
                    if m['macro'] == '{$PRICE}':
                        m['value'] = round(host['price'], 6)
                        break
                macros['{$PRICE}'] =round(host['price'], 6)
                changed = True
                loggerMessage = ("[ZAPI] [host_update_instance_price] "
                                 + "The price of host " + host['id']
                                 + " has been changed: "
                                 + lastprice + " -> "
                                 + str(round(host['price'], 6)))
        # If the PRICE is not present, we add it
        else:
            host['macros_zabbix'].append({'macro': '{$PRICE}',
                                          'value':
                                          str(round(host['price'], 6))})
            host['macros']['{$PRICE}'] = round(host['price'], 6)
            changed = True
            loggerMessage = ("[ZAPI] [host_update_instance_price] The price "
                             + "of host " + host['id']
                             + " added: "
                             + str(round(host['price'], 6)))

        if changed:
            try:
                os.system("zabbix_sender -z " + str(IPSERVER) + " -s "
                          + host['id'] + " -k cloud.price -o "
                          + str(round(host['price'], 6)))
                zapi.host.update(hostid=host['id_zabbix'],
                                 macros=host['macros_zabbix'])
            except pyzabbix.ZabbixAPIException as e:
                logger.error("[ZAPI] [host_update_instance_price] Could not "
                             + "update price of the host "
                             + host['id'] + " :" + str(e))
            else:
                logger.info(loggerMessage)

        history_price = get_history(host=host, itemkey='cloud.price',
                                    since=0, till=NOW, limit=1)
        if not history_price:
            os.system("zabbix_sender -z " + str(IPSERVER) + " -s "
                      + host['id'] + " -k cloud.price -o "
                      + str(round(host['price'], 6)))


# Update type of a host
def host_update_type(host):
    macros = host['macros']
    changed = False
    # If the TYPE macro is present
    if '{$TYPE}' in macros:
        # Check its consistency, if different update the macro and template
        if macros['{$TYPE}'] != host['type']:
            lasttype = macros['{$TYPE}']
            for m in host['macros_zabbix']:
                if m['macro'] == '{$TYPE}':
                    m['value'] = host['type']
                    break
            macros['{$TYPE}'] = host['type']
            changed = True
            loggerMessage = ("[ZAPI] [host_update_type] The type of host "
                             + host['id'] + " has been changed: "
                             + lasttype + " -> " + host['type'])
    # If the TYPE is not present, we add it
    else:
        host['macros_zabbix'].append({'macro': '{$TYPE}',
                                      'value': str(host['type'])})
        host['macros']['{$TYPE}'] = host['type']
        changed = True
        loggerMessage = ("[ZAPI] [host_update_type] The type of host "
                         + host['id'] + " added: " + host['type'])
    if changed:
        try:
            zapi.host.update(hostid=host['id_zabbix'],
                             macros=host['macros_zabbix'])
        except pyzabbix.ZabbixAPIException as e:
            logger.error("[ZAPI] [host_update_type] Could not update macros "
                         + "of the host " + host['id'] + ": " + str(e))
        else:
            logger.info(loggerMessage)


def host_update_template(host, newTemplateName, oldTemplateName):
    try:
        newTemplateID = get_templateID(newTemplateName)
        oldTemplateID = None
        if oldTemplateName:
            oldTemplateID = get_templateID(oldTemplateName)
    except (pyzabbix.ZabbixAPIException, NotFoudException) as e:
        if oldTemplateName:
            logger.error("[ZAPI] [host_update_family] Could not find template "
                         + newTemplateName + " or "
                         + oldTemplateName + ": " + str(e))
        else:
            logger.error("[ZAPI] [host_update_family] Could not find template "
                         + newTemplateName + ": " + str(e))
    else:
        if oldTemplateName:
            del host['templates'][oldTemplateName]
        host['templates'][newTemplateName] = {}
        host['templates'][newTemplateName]['templateid'] = newTemplateID
        host['templates'][newTemplateName]['name'] = newTemplateName

        for t in host['templates_zabbix']:
            if t['templateid'] == oldTemplateID:
                host['templates_zabbix'].remove(t)
                break
        host['templates_zabbix'].append({'templateid': newTemplateID,
                                         'name': newTemplateName})
        try:
            zapi.host.update(hostid=host['id_zabbix'],
                             templates=host['templates_zabbix'])
        except pyzabbix.ZabbixAPIException as e:
            logger.error("[ZAPI] [host_update_family] Could not "
                         + "update template of the host "
                         + host['id'] + ": " + str(e))
        else:
            if oldTemplateName:
                logger.info("[ZAPI] [host_update_family] The template "
                            + "of host " + host['id'] + " has been "
                            + "changed: " + oldTemplateName
                            + " -> " + newTemplateName)
            else:
                logger.info("[ZAPI] [host_update_family] The template "
                            + "of host " + host['id'] + " has been "
                            + "added: " + newTemplateName)


# Update type of a host
def host_update_family(host):
    macros = host['macros']
    changed = False

    lastfamily = None
    # If the FAMILY macro is present
    if '{$FAMILY}' in macros:
        # Check its consistency, if different update the macro and template
        if macros['{$FAMILY}'] != host['family']:
            changed = True
            lastfamily = macros['{$FAMILY}']
            for m in host['macros_zabbix']:
                if m['macro'] == '{$FAMILY}':
                    m['value'] = host['family']
                    break
            macros['{$FAMILY}'] = host['family']
            loggerMessage = ("[ZAPI] [host_update_family] The family of host "
                             + host['id'] + " has been changed: "
                             + lastfamily + " -> " + host['family'])
    # If the FAMILY is not present, we add it
    else:
        host['macros_zabbix'].append({'macro': '{$FAMILY}',
                                      'value': str(host['family'])})
        host['macros']['{$FAMILY}'] = host['family']
        changed = True
        loggerMessage = ("[ZAPI] [host_update_family] The family of host "
                         + host['id'] + " added: " + host['family'])
    if changed:
        try:
            zapi.host.update(hostid=host['id_zabbix'],
                             macros=host['macros_zabbix'])
        except pyzabbix.ZabbixAPIException as e:
            logger.error("[ZAPI] [host_update_family] Could not update macros "
                         + "of the host " + host['id'] + ": " + str(e))
        else:
            # Change the tamplate
            logger.info(loggerMessage)
            if lastfamily:
                oldTemplate = None
                newTemplate = (host['provider'] + '-' + host['family']
                               + '-template')
                for t in host['templates']:
                    if t.find(lastfamily) != -1:
                        oldTemplate = t
                host_update_template(host, newTemplate, oldTemplate)


# Get history from a item
def get_history(host, itemkey=None, itemid=None, since=None, till=None,
                limit=None, output=['itemid', 'clock', 'value']):
    # If item key, get the id
    if itemkey:
        itemid = host['items'][itemkey]['itemid']
    # If item id, find out the name if do not have it
    elif itemid:
        if not itemkey:
            for i in host['items']:
                if host['items'][i]['itemid'] == itemid:
                    itemkey = host['items'][i]['key_']
    # If do not have itemkey nor itemid, it is an error
    else:
        logger.error("[ZAPI] [get_history] an item key or item id is required")
        return

    try:
        values = zapi.history.get(itemids=itemid,
                                  history=host['items'][itemkey]['value_type'],
                                  time_from=since+1,
                                  time_till=till,
                                  sortorder='DESC',
                                  limit=limit,
                                  output=output)
    except pyzabbix.ZabbixAPIException as e:
        logger.error("[ZAPI] [get_history] Could not get history of item "
                     + itemkey + "of the host " + host['id'] + ": " + str(e))
    else:
        for v in values:
            v['timestamp'] = int(v['clock'])
            del v['clock']
        return values


# This function associates each device to its filesystem
def associate_filesystem_device(host):
    host['devices_without_filesystems'] = [d['device']
                                           for d in host['devices']]
    host['filesystems_without_devices'] = host['filesystems']
    # If provider is AWS and os is Linux we can do the association
    if host['provider'] == 'aws' and host['os'] == 'Linux':
        association = {}
        devices = []
        for d in [d['device'] for d in host['devices']]:
            base = None
            trailing_letter = None
            if d.find('/dev/sd') != -1:
                base = '/dev/sd'
                trailing_letter = re.sub('/dev/sd', '', d)
            elif d.find('/dev/hd') != -1:
                base = '/dev/hd'
                trailing_letter = re.sub('/dev/hd', '', d)
            else:
                logger.error("[ZAPI] [associate_filesystem_device] Could not "
                             + "find base for device " + d)
                return
            devices.append([base, trailing_letter])
        filesystems = []
        for f in host['filesystems']:
            base = None
            trailing_letter = None
            if f.find('/dev/xvd') != -1:
                base = '/dev/xvd'
                trailing_letter = re.sub('/dev/xvd', '', f)
            else:
                logger.error("[ZAPI] [associate_filesystem_device] Could not "
                             + " find base for filesystem " + f)
                return
            filesystems.append([base, trailing_letter])

        # Get the root
        for d in devices.copy():
            for f in filesystems.copy():
                if d[1] == f[1]:
                    association[d[0]+d[1]] = f[0] + f[1]
                    devices.remove(d)
                    filesystems.remove(f)

        host['devices_without_filesystems'] = []
        for d in devices:
            host['devices_without_filesystems'].append(d[0]+d[1])
        host['filesystems_without_devices'] = []
        for f in filesystems:
            host['filesystems_without_devices'].append(f[0]+f[1])
        host['devices_filesystems'] = association


# Update filesystems of host
# This macro is a dict, associating each device to its filesystem
def host_update_devices(host):
    associate_filesystem_device(host)

    macros = host['macros']
    changed = False
    # If the DEVICES macro is present
    if '{$DEVICES}' in macros:
        # Check its consistency, if different update the macro and template
        if macros['{$DEVICES}'] != str(host['devices_filesystems']):
            lastdevices = macros['{$DEVICES}']
            for m in host['macros_zabbix']:
                if m['macro'] == '{$TYPE}':
                    m['value'] = str(host['devices_filesystems'])
                    break
            macros['{$DEVICES}'] = str(host['devices_filesystems'])
            changed = True
            loggerMessage = ("[ZAPI] [host_update_devices] The devices of host"
                             + " " + host['id'] + " has been changed: "
                             + lastdevices + " -> "
                             + str(host['devices_filesystems']))
    # If the TYPE is not present, we add it
    else:
        host['macros_zabbix'].append({'macro': '{$DEVICES}',
                                      'value': str(host['devices_filesystems'])
                                      })
        host['macros']['{$DEVICES}'] = str(host['devices_filesystems'])
        changed = True
        loggerMessage = ("[ZAPI] [host_update_devices] The devices of host "
                         + host['id'] + " added: "
                         + str(host['devices_filesystems']))
    if changed:
        try:
            zapi.host.update(hostid=host['id_zabbix'],
                             macros=host['macros_zabbix'])
        except pyzabbix.ZabbixAPIException as e:
            logger.error("[ZAPI] [host_update_devices] Could not update macros"
                         + " of the host " + host['id'] + ": " + str(e))
        else:
            logger.info(loggerMessage)


# Update price of a filesystem
def host_update_filesystem_price(volume, host):
    # If there is a price
    if volume['price']:
        # Get the device nome of volume
        device_name = volume['attachment']['device']
        if device_name not in host['devices_filesystems']:
            logger.error("[ZAPI] [host_update_filesystem_price] "
                         + " This volume is not mounted "
                         + volume['attachment']['device'])
            return

        # Get the item history
        itemkey = 'vfs.fs.price['+host['devices_filesystems'][device_name]+']'
        history_price = get_history(host=host, since=0, till=NOW,
                                    itemkey=itemkey, limit=1)
        # Add or update the price
        if (not history_price
           or float(history_price[0]['value']) != round(volume['price'], 6)):
            os.system("zabbix_sender -z " + str(IPSERVER) + " -s "
                      + volume['attachment']['instance']
                      + " -k " + itemkey + " -o "
                      + str(volume['price']))
