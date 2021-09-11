"""
Authors: William Felipe C. Tavares, Marcio Roberto Miranda Assis, Edson Borin
Copyright Unicamp
"""
import os
import logging
import zapi as monitorserver
import awsapi as aws
from pprint import pprint
from datetime import datetime, timedelta
import pytz
from sendemail import (notregistered_email, availablevolume_email,
                       usernotfound_email)


# Setting Log File
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

#-------------------------------------------------------
# Setting of constants
STOPPED_INSTANCES_FILE = home+"/files/stopped-instances.hosts"
NOTREGISTERED_INSTANCES_FILE = home+"/files/notregistered-instances.hosts"
NOTREGISTERED_INSTANCES_TIME_TO_NOTIFY = timedelta(minutes=10)
AVAILABLE_VOLUMES_FILE = home+"/files/available-volumes.hosts"
AVAILABLE_VOLUMES_FIRST_TIME_TO_NOTIFY = timedelta(hours=3)
AVAILABLE_VOLUMES_TIME_TO_NOTIFY = timedelta(days=4)
NOTREGISTERED_USERS_FILE = home+"/files/notregistered-users.users"
NOTREGISTERED_USERS_TIME_TO_NOTIFY = timedelta(minutes=30)
STARTING_INSTANCES_TIME_TO_NOTIFY = timedelta(minutes=6)
#-------------------------------------------------------

NOW = datetime.utcnow().astimezone(pytz.utc)

# This function reads a history file
def read_history_file(FILE_NAME):
    objectsFromFile = []
    if os.path.isfile(FILE_NAME):
        objectsFromFile = (open(str(FILE_NAME), "r")).read().splitlines()
    objects = {}
    for object in [x.split(",") for x in objectsFromFile if x]:
        objects[object[0]] = datetime.strptime(object[1],
                                               '%Y-%m-%d %H:%M:%S %z')
    return objects


# This function writes into a history file
def write_history_file(FILE_NAME, objects):
    f = open(str(FILE_NAME), "w")
    for object in objects:
        f.write(str(object)+'\n')
    f.close()


# Get users from Monitor Server
users = monitorserver.get_users()

# Get instances from providers
providers = (open(home+'/private/providers', "r")).read().splitlines()
instances = []
for p in providers:
    if p == 'aws':
        instances.extend(aws.get_instances(ignore={
                                        'tags': {'monitorignore': ['True', 'true']},
                                        'state': ['terminated', 'shutting-down']}))
print(instances)
hostsFromProvider = {}
hostsFromProviderStopped = {}
hostsFromProviderUserNotRegistered = {}
# For each instance, check if the user(user) is registered on Monitor Server
for instance in instances:
    if NOW - instance['launchtime'] > STARTING_INSTANCES_TIME_TO_NOTIFY:
        if instance['provider'] in ['aws']:
            # If the instance is stopped or stopping
            if instance['state'] in ['stopped', 'stopping']:
                if instance['user'] in users:
                    hostsFromProviderStopped[instance['id']] = {
                                        'id': instance['id'],
                                        'launchtime': instance['launchtime']
                                        }
            # If the instance is running
            elif instance['state'] in ['running', 'pending']:
                # If its from a user not registered
                if instance['user'] in users:
                    hostsFromProvider[instance['id']] = {
                                'id': instance['id'],
                                'user': instance['user'],
                                'type': instance['type'],
                                'family': instance['family'],
                                'provider': instance['provider'],
                                'region': instance['region'],
                                'service': instance['service'],
                                'service_id': instance['service_id'],
                                'price': instance['price'],
                                'launchtime': instance['launchtime']
                                }
                else:
                    hostsFromProviderUserNotRegistered[instance['id']] = {
                                            'id': instance['id'],
                                            'user': instance['user']}


hostsFromMonitorServer = monitorserver.get_hosts(
                                        resource='virtualmachines',
                                        output=['name'],
                                        filter={'status': '0'},
                                        macros=['macro', 'value'],
                                        triggers=['triggerid', 'name'],
                                        )

# Get the attributes from provider
for host in [x for x in hostsFromMonitorServer if x in hostsFromProvider]:
    hostsFromMonitorServer[host]['user'] = hostsFromProvider[host]['user']
    hostsFromMonitorServer[host]['provider'] = hostsFromProvider[host][
                                                                'provider']
    hostsFromMonitorServer[host]['region'] = hostsFromProvider[host]['region']
    hostsFromMonitorServer[host]['type'] = hostsFromProvider[host]['type']
    hostsFromMonitorServer[host]['family'] = hostsFromProvider[host]['family']
    hostsFromMonitorServer[host]['service'] = hostsFromProvider[host][
                                                                'service']
    hostsFromMonitorServer[host]['service_id'] = hostsFromProvider[host][
                                                                'service_id']
    hostsFromMonitorServer[host]['price'] = hostsFromProvider[host]['price']
    hostsFromMonitorServer[host]['launchtime'] = hostsFromProvider[host][
                                                                'launchtime']


# -----------------------------------------------------------------------------
# Get not registered users from file
notregisteredUsers = read_history_file(NOTREGISTERED_USERS_FILE)

# Detect users using Monitoring System but not registered on the Monitor Server
newNotregisteredUsers = []
usersAlreadyNotified = []
for host in {host for host in hostsFromMonitorServer
             if host in hostsFromProviderUserNotRegistered}:
    user = hostsFromProviderUserNotRegistered[host]['user']
    # If the user has already been checked
    if user in usersAlreadyNotified:
        continue
    usersAlreadyNotified.append(user)
    # If the admins have not been notified about user in the last notification
    # time period, we notify the admins
    if (user not in [x for x in notregisteredUsers]
            or (NOW - notregisteredUsers[user]
                > NOTREGISTERED_USERS_TIME_TO_NOTIFY)):
        del hostsFromMonitorServer[host]
        try:
            emails = monitorserver.get_admins_email()
            usernotfound_email(emails, user)
        except (monitorserver.NotFoudException, KeyError) as e:
            logger.error("[AUDIT] Not registered user. " + user
                         + "Could not send email to admins: " + str(e))
        else:
            newNotregisteredUsers.append(str(user) + ',' +
                                         + NOW.strftime(
                                         "%Y-%m-%d %H:%M:%S %z"))
            logger.info("[AUDIT] This user is not registered: "
                        + user + ". Sending email to admins")
    else:
        newNotregisteredUsers.append(str(user) + ','
                                     + notregisteredUsers[user].strftime(
                                     "%Y-%m-%d %H:%M:%S %z"))
        del hostsFromMonitorServer[host]

# Write file with not registered users
write_history_file(NOTREGISTERED_USERS_FILE, newNotregisteredUsers)


# -----------------------------------------------------------------------------
# Get stopped instances from file
stoppedInstances = read_history_file(STOPPED_INSTANCES_FILE)

# Disable triggers of new stopped instances
newStoppedInstances = []
for host in hostsFromProviderStopped:
    if host in hostsFromMonitorServer and host not in stoppedInstances:
        monitorserver.host_triggers_disable(hostsFromMonitorServer[host])
    newStoppedInstances.append(hostsFromProviderStopped[host]['id'] + ','
                               + hostsFromProviderStopped[host][
                                                    'launchtime'].strftime(
                                                    "%Y-%m-%d %H:%M:%S %z"))

# Write the current stopped instances into the file
write_history_file(STOPPED_INSTANCES_FILE, newStoppedInstances)

# Enable triggers of instances that are not stopped anymore
for host in stoppedInstances:
    if host in hostsFromMonitorServer and host not in hostsFromProviderStopped:
        monitorserver.host_triggers_enable(hostsFromMonitorServer[host])

# -----------------------------------------------------------------------------
# Get not registered instances from file
notregisteredInstances = read_history_file(NOTREGISTERED_INSTANCES_FILE)

# Detect instances that are not registered on the Monitor Server
newNotregisteredInstances = []
for host in [x for x in hostsFromProvider if x not in hostsFromMonitorServer]:
    # If the admins and user have not been notified about this instance in the
    # last notification time period, we notify the admins and user
    if (host not in [x for x in notregisteredInstances]
            or (NOW - notregisteredInstances[host]
                > NOTREGISTERED_INSTANCES_TIME_TO_NOTIFY)):
        try:
            emails = monitorserver.get_admins_email()
            emails.append(monitorserver.get_user_email(hostsFromProvider[
                                                        host]['user']))
            notregistered_email(emails, host)
        except monitorserver.NotFoudException as e:
            logger.error("[AUDIT] Not registered host " + host
                         + ". Could not send email to admins and user "
                         + hostsFromProvider[host]['user'] + ": "
                         + str(e))
        else:
            newNotregisteredInstances.append(host + ','
                                             + NOW.strftime(
                                              "%Y-%m-%d %H:%M:%S %z"))
            logger.info("[AUDIT] This instance is not registered: "
                        + host + ". Sending email to admins and user "
                        + hostsFromProvider[host]['user'])
    else:
        newNotregisteredInstances.append(host + ','
                                         + notregisteredInstances[
                                            host].strftime(
                                            "%Y-%m-%d %H:%M:%S %z"))

# Write file with not registered instances
write_history_file(NOTREGISTERED_INSTANCES_FILE, newNotregisteredInstances)

# -----------------------------------------------------------------------------
# Get volumes from provider
volumes = []
for p in providers:
    if p == 'aws':
        volumes.extend(aws.get_volumes(ignore={'tags': {'monitorignore': ['True', 'true']}}))


# For each volume, we check if the user(user) is registered on Monitor Server
volumesFromProvider = []
volumesFromProviderAvailable = []
for volume in volumes:
    if volume['provider'] in ['aws']:
        if volume['user'] in users:
            if volume['state'] in ['in-use']:
                volumesFromProvider.append(
                                    {'id': volume['id'],
                                     'user': volume['user'],
                                     'type': volume['type'],
                                     'region': volume['region'],
                                     'provider': volume['provider'],
                                     'attachment': volume['attachment'],
                                     'launchtime': volume['launchtime'],
                                     'price': volume['price']
                                     })
            elif volume['state'] in ['available']:
                volumesFromProviderAvailable.append(
                                    {'id': volume['id'],
                                     'user': volume['user'],
                                     'type': volume['type'],
                                     'region': volume['region'],
                                     'provider': volume['provider'],
                                     'detachment': volume['detachment'],
                                     'launchtime': volume['launchtime'],
                                     'price': volume['price']
                                     })


# Get volumes from Monitor Server
volumesFromMonitorServer = monitorserver.get_hosts(
                                                resource='volumes',
                                                output=['name'],
                                                filter={'status': '0'},
                                                macros=['macro', 'value'],
                                                triggers=['triggerid', 'name'],
                                                )

# Get available volumes from file
availableVolumes = read_history_file(AVAILABLE_VOLUMES_FILE)

# Detect volumes that are available for too long
nowAvailableVolumes = []
for volume in volumesFromProviderAvailable:
    # If the volume has been detached for a little while, ignore
    if (volume['detachment']
        and NOW - volume['detachment']
            < AVAILABLE_VOLUMES_FIRST_TIME_TO_NOTIFY):
        continue
    # If the admins and user have not been notified about this volume in the
    # last notification time period, we notify the admins and user
    if (volume['id'] not in [x for x in availableVolumes]
            or (NOW - availableVolumes[volume['id']]
                > AVAILABLE_VOLUMES_TIME_TO_NOTIFY)):
        try:
            emails = monitorserver.get_admins_email()
            emails.append(monitorserver.get_user_email(volume['user']))
            availablevolume_email(emails, volume['id'])
        except monitorserver.NotFoudException as e:
            logger.error("[AUDIT] Volume available for too long "
                         + volume['id']
                         + ". Could not send email to admins and user "
                         + volume['user']
                         + ": " + str(e))
        else:
            nowAvailableVolumes.append(volume['id'] + ','
                                       + NOW.strftime("%Y-%m-%d %H:%M:%S %z"))
            logger.info("[AUDIT] This volume is available for too long: "
                        + volume['id'] + ". Sending email to admins and user "
                        + volume['user'])
    else:
        nowAvailableVolumes.append(volume['id'] + ','
                                   + availableVolumes[volume['id']].strftime(
                                   "%Y-%m-%d %H:%M:%S %z"))

# Write file with available volumes
write_history_file(AVAILABLE_VOLUMES_FILE, nowAvailableVolumes)
