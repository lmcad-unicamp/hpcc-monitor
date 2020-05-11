import os
import logging
import zapi as monitorserver
import awsapi as aws
from sendemail import (notregistered_email, availablevolume_email,
                       usernotfound_email)
from datetime import datetime, timedelta
from pprint import pprint

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

# Setting of constants
STOPPED_INSTANCES_FILE = home+"/files/stopped-instances.hosts"
NOTREGISTERED_INSTANCES_FILE = home+"/files/notregistered-instances.hosts"
NOTREGISTERED_INSTANCES_TIME_TO_NOTIFY = timedelta(minutes=10)
AVAILABLE_VOLUMES_FILE = home+"/files/available-volumes.hosts"
AVAILABLE_VOLUMES_TIME_TO_NOTIFY = timedelta(weeks=1)
NOTREGISTERED_USERS_FILE = home+"/files/notregistered-users.users"
NOTREGISTERED_USERS_TIME_TO_NOTIFY = timedelta(minutes=30)
STARTING_INSTANCES_TIME_TO_NOTIFY = timedelta(minutes=6)
NOW = datetime.utcnow().replace(tzinfo=None)

# Get users from Monitor Server
users = monitorserver.get_users()

# Get instances and volume from providers
instances = aws.get_instances(ignore={'tags': {'monitorignore':
                                               ['True', 'true']},
                                      'state': ['terminated',
                                                'shutting-down']})
volumes = aws.get_volumes()

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

# For each volume, we check if the user(user) is registered on Monitor Server,
# and check if it is monitor ignore
volumesFromProvider = []
volumesFromProviderAvailable = []
for volume in volumes:
    if volume['monitorignore']:
        continue
    if volume['provider'] in ['aws']:
        if volume['user'] in users:
            if volume['state'] in ['in-use']:
                volumesFromProvider.append(
                                    {'id': volume['id'],
                                     'user': volume['user'],
                                     'type': volume['type'],
                                     'region': volume['region'],
                                     'provider': volume['provider'],
                                     'attachments': volume['attachments'],
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
                                     'launchtime': volume['launchtime'],
                                     'price': volume['price']
                                     })

hostsFromMonitorServer = monitorserver.get_hosts(
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
notregisteredUsersFromFile = []
if os.path.isfile(NOTREGISTERED_USERS_FILE):
    notregisteredUsersFromFile = (open(str(NOTREGISTERED_USERS_FILE), "r")
                                  ).read().splitlines()
notregisteredUsers = {}
for notregistered in [x.split(',') for x in notregisteredUsersFromFile]:
    notregisteredUsers[notregistered[0]] = datetime.strptime(
                                                        notregistered[1],
                                                        '%Y-%m-%d %H:%M:%S.%f')

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
            or NOW - notregisteredUsers[user] >
            NOTREGISTERED_USERS_TIME_TO_NOTIFY):
        usersAlreadyNotified.append(user)
        del hostsFromMonitorServer[host]
        try:
            emails = monitorserver.get_admins_email()
            #usernotfound_email(emails, user)
        except (monitorserver.NotFoudException, KeyError) as e:
            logger.error("[AUDIT] Not registered user. " + user
                         + "Could not send email to admins: " + str(e))
        else:
            newNotregisteredUsers.append(str(user) + ',' + str(NOW))
            logger.info("[AUDIT] This user is not registered: "
                        + user + ". Sending email to admins")
    else:
        newNotregisteredUsers.append(str(user) + ','
                                     + str(notregisteredUsers[user]))
        del hostsFromMonitorServer[host]

# Write file with not registered users
f = open(str(NOTREGISTERED_USERS_FILE), "w")
for notregistered in newNotregisteredUsers:
    f.write(str(notregistered)+'\n')
f.close()


# -----------------------------------------------------------------------------
# Get stopped instances from file
stoppedInstancesFromFile = []
if os.path.isfile(STOPPED_INSTANCES_FILE):
    stoppedInstancesFromFile = (open(str(STOPPED_INSTANCES_FILE), "r")
                                ).read().splitlines()
stoppedInstances = {}
for stopped in [x.split(",") for x in stoppedInstancesFromFile if x]:
    stoppedInstances[stopped[0]] = datetime.strptime(stopped[1],
                                                     '%Y-%m-%d %H:%M:%S')

# Write the current stopped instances into the file
f = open(str(STOPPED_INSTANCES_FILE), "w")
for host in hostsFromProviderStopped:
    f.write(hostsFromProviderStopped[host]['id'] + ','
            + str(hostsFromProviderStopped[host]['launchtime'])+'\n')
f.close()

# Disable triggers of new stopped instances
for host in hostsFromProviderStopped:
    if host in hostsFromMonitorServer and host not in stoppedInstances:
        monitorserver.host_triggers_disable(hostsFromMonitorServer[host])

# Enable triggers of instances that are not stopped anymore
for host in stoppedInstances:
    if host in hostsFromMonitorServer and host not in hostsFromProviderStopped:
        monitorserver.host_triggers_enable(hostsFromMonitorServer[host])

# -----------------------------------------------------------------------------

# Get not registered instances from file
notregisteredInstancesFromFile = []
if os.path.isfile(NOTREGISTERED_INSTANCES_FILE):
    notregisteredInstancesFromFile = (open(str(NOTREGISTERED_INSTANCES_FILE),
                                           "r")).read().splitlines()
notregisteredInstances = {}
for notregistered in [x.split(',')
                      for x in notregisteredInstancesFromFile if x]:
    notregisteredInstances[notregistered[0]] = datetime.strptime(
                                                        notregistered[1],
                                                        '%Y-%m-%d %H:%M:%S.%f')

# Detect instances that are not registered on the Monitor Server
newNotregisteredInstances = []
for host in [x for x in hostsFromProvider if x not in hostsFromMonitorServer]:
    # If the admins and user have not been notified about this instance in the
    # last notification time period, we notify the admins and user
    if (host not in [x for x in notregisteredInstances]
            or NOW - notregisteredInstances[host]
            > NOTREGISTERED_INSTANCES_TIME_TO_NOTIFY):
        try:
            emails = monitorserver.get_admins_email()
            emails.append(monitorserver.get_user_email(hostsFromMonitorServer[
                                                        host]['user']))
            notregistered_email(emails, host)
        except monitorserver.NotFoudException as e:
            logger.error("[AUDIT] Not registered host " + host
                         + ". Could not send email to admins and user "
                         + hostsFromMonitorServer[host]['user'] + ": "
                         + str(e))
        else:
            newNotregisteredInstances.append(host + ',' + str(NOW))
            logger.info("[AUDIT] This instance is not registered: "
                        + host + ". Sending email to admins and user "
                        + hostsFromMonitorServer[host]['user'])
    else:
        newNotregisteredInstances.append(host + ','
                                         + str(notregisteredInstances[host]))

# Write file with not registered instances
f = open(str(NOTREGISTERED_INSTANCES_FILE), "w")
for notregistered in newNotregisteredInstances:
    f.write(str(notregistered)+'\n')
f.close()

# -----------------------------------------------------------------------------

# Get available volumes from file
availableVolumesFromFile = []
if os.path.isfile(AVAILABLE_VOLUMES_FILE):
    availableVolumesFromFile = (open(str(AVAILABLE_VOLUMES_FILE), "r")
                                ).read().splitlines()
availableVolumes = {}
for available in [x.split(',') for x in availableVolumesFromFile if x]:
    availableVolumes[available[0]] = datetime.strptime(available[1],
                                                       '%Y-%m-%d %H:%M:%S.%f')

# Detect volumes that are available for too long
nowAvailableVolumes = []
for volume in volumesFromProviderAvailable:
    # If the admins and user have not been notified about this volume in the
    # last notification time period, we notify the admins and user
    if (volume['id'] not in [x for x in availableVolumes]
            or (NOW - availableVolumes[volume['id']]
                > AVAILABLE_VOLUMES_TIME_TO_NOTIFY)):
        try:
            emails = monitorserver.get_admins_email()
            emails.append(monitorserver.get_user_email(volume['user']))
            # availablevolume_email(emails, volume)
        except monitorserver.NotFoudException as e:
            logger.error("[AUDIT] Volume available for too long " + volume
                         + ". Could not send email to admins and user "
                         + volume['user']
                         + ": " + str(e))
        else:
            nowAvailableVolumes.append(volume['id'] + ',' + str(NOW))
            logger.info("[AUDIT] This volume is available for too long: "
                        + volume['id'] + ". Sending email to admins and user "
                        + volume['user'])
    else:
        nowAvailableVolumes.append(volume['id'] + ','
                                   + str(availableVolumes[volume['id']]))

# Write file with available volumes
f = open(str(AVAILABLE_VOLUMES_FILE), "w")
for available in nowAvailableVolumes:
    f.write(str(available)+'\n')
f.close()
