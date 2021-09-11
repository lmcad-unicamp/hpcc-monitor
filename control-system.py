"""
Authors: William Felipe C. Tavares, Marcio Roberto Miranda Assis, Edson Borin
Copyright Unicamp
"""
import os
import logging
import zapi as monitorserver
import awsapi as aws
from pprint import pprint

# Setting Log File
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

# Gets users from Monitor Server
users = monitorserver.get_users()

# Gets instances and volumes from providers
providers = (open(home+'/private/providers', "r")).read().splitlines()
    
instances = []
for p in providers:
    if p == "aws":
        instances.extend(aws.get_instances(pricing=True, 
                        ignore={'tags': {'monitorignore': ['True', 'true']},
                              'state': ['terminated', 'shutting-down'],
                              'price': {'state': ['stopped', 'stopping']}}))

hostsFromProvider = {}
hostsFromProviderStopped = {}
hostsFromProviderUserNotRegistered = {}
# For each instance, we check if the user(user) is registered on Monitor Server
for instance in instances:
    if instance['provider'] in ['aws']:
        # If the instance is stopped or stopping
        if instance['state'] in ['stopped', 'stopping']:
            if instance['user'] in users:
                hostsFromProviderStopped[instance['id']] = {
                            'id': instance['id'],
                            'resource': 'virtualmachines',
                            'user': instance['user'],
                            'type': instance['type'],
                            'family': instance['family'],
                            'provider': instance['provider'],
                            'region': instance['region'],
                            'os': instance['os'],
                            'service': instance['service'],
                            'service_id': instance['service_id'],
                            'devices': instance['devices'],
                            'price': instance['price'],
                            'launchtime': instance['launchtime'],
                            'restartlaunchtime': instance['restartlaunchtime']
                            }
        # If the instance is running
        elif instance['state'] in ['running', 'pending']:
            # If its from a user not registered
            if instance['user'] not in users:
                hostsFromProviderUserNotRegistered[instance['id']] = {
                                        'id': instance['id'],
                                        'user': instance['user']}
            hostsFromProvider[instance['id']] = {
                            'id': instance['id'],
                            'resource': 'virtualmachines',
                            'user': instance['user'],
                            'type': instance['type'],
                            'family': instance['family'],
                            'provider': instance['provider'],
                            'region': instance['region'],
                            'os': instance['os'],
                            'service': instance['service'],
                            'service_id': instance['service_id'],
                            'devices': instance['devices'],
                            'price': instance['price'],
                            'launchtime': instance['launchtime'],
                            'restartlaunchtime': instance['restartlaunchtime']
                            }

hostsFromMonitorServer = monitorserver.get_hosts(
                                        resource='virtualmachines',
                                        output=['name'],
                                        filter={'status': '0'},
                                        macros=['macro', 'value'],
                                        templates=['templateid', 'name'],
                                        items=['itemid', 'key_', 'value_type'],
                                        groups=['groupsid', 'name'],
                                        filesystems=True
                                        )

# If the instance is stopped, we are not going to handle it here
stoppedHostFromMonitorServer = {}
for host in {host for host in hostsFromMonitorServer
             if host in hostsFromProviderStopped}:
    stoppedHostFromMonitorServer[host] = hostsFromMonitorServer[host]
    del hostsFromMonitorServer[host]

# Detect terminated instances and disable it on Monitor Server
for host in {host for host in hostsFromMonitorServer
             if host not in hostsFromProvider}:
    monitorserver.host_disable(hostsFromMonitorServer[host])
    del hostsFromMonitorServer[host]

# Gets the attributes from provider
for host in hostsFromMonitorServer:
    hostsFromMonitorServer[host]['user'] = hostsFromProvider[host]['user']
    hostsFromMonitorServer[host]['resource'] = hostsFromProvider[host][
                                                                'resource']
    hostsFromMonitorServer[host]['provider'] = hostsFromProvider[host][
                                                                'provider']
    hostsFromMonitorServer[host]['region'] = hostsFromProvider[host]['region']
    hostsFromMonitorServer[host]['type'] = hostsFromProvider[host]['type']
    hostsFromMonitorServer[host]['family'] = hostsFromProvider[host]['family']
    hostsFromMonitorServer[host]['os'] = hostsFromProvider[host]['os']
    hostsFromMonitorServer[host]['service'] = hostsFromProvider[host][
                                                                'service']
    hostsFromMonitorServer[host]['service_id'] = hostsFromProvider[host][
                                                                'service_id']
    hostsFromMonitorServer[host]['devices'] = hostsFromProvider[host][
                                                                'devices']
    hostsFromMonitorServer[host]['price'] = hostsFromProvider[host]['price']
    hostsFromMonitorServer[host]['launchtime'] = hostsFromProvider[host][
                                                                'launchtime']
    hostsFromMonitorServer[host]['restartlaunchtime'] = (
                                hostsFromProvider[host]['restartlaunchtime'])

# Associate the user with the host when the user is registered
for host in hostsFromMonitorServer:
    if host not in hostsFromProviderUserNotRegistered:
        monitorserver.host_user_association(hostsFromMonitorServer[host])

# Associate the host with its provider, region, launchtime, os
# Update price, type, family and devices
for host in hostsFromMonitorServer:
    monitorserver.host_provider_association(hostsFromMonitorServer[host])
    monitorserver.host_region_association(hostsFromMonitorServer[host])
    monitorserver.host_service_association(hostsFromMonitorServer[host])
    monitorserver.host_os_association(hostsFromMonitorServer[host])
    monitorserver.host_update_family(hostsFromMonitorServer[host])
    monitorserver.host_update_type(hostsFromMonitorServer[host])
    monitorserver.host_launchtime_association(hostsFromMonitorServer[host])
    monitorserver.host_update_restartlaunchtime(hostsFromMonitorServer[host])
    monitorserver.host_update_devices_filesystems(hostsFromMonitorServer[host])
    monitorserver.host_update_price(hostsFromMonitorServer[host])

# -------------------------------------------------------------------------

# Get volumes from provider
volumes = []
for p in providers:
    if p == 'aws':
        volumes.extend(aws.get_volumes(pricing=True,
                          ignore={'tags': {'monitorignore': ['True', 'true']},
                                  'state': ['error', 'creating',
                                            'deleted', 'deleting']}))


# For each volume, we check if the user(user) is registered on Monitor Server
volumesFromProvider = {}
for volume in volumes:
    if volume['provider'] in ['aws']:
        if volume['user'] in users:
            volumesFromProvider[volume['id']] = {
                                    'id': volume['id'],
                                    'resource': 'volumes',
                                    'user': volume['user'],
                                    'size': volume['size'],
                                    'type': volume['type'],
                                    'region': volume['region'],
                                    'provider': volume['provider'],
                                    'attachment': volume['attachment'],
                                    'detachment': volume['detachment'],
                                    'launchtime': volume['launchtime'],
                                    'price': volume['price']}

# Get volumes from Monitor Server
volumesFromMonitorServer = monitorserver.get_hosts(
                                        resource='volumes',
                                        output=['name'],
                                        filter={'status': '0'},
                                        macros=['macro', 'value'],
                                        triggers=['triggerid', 'name'],
                                        items=['itemid', 'key_', 'value_type'],
                                        groups=['groupsid', 'name'],
                                        )

# Register new volumes on Monitor Server
for volume in [volume for volume in volumesFromProvider
               if volume not in volumesFromMonitorServer]:
    monitorserver.register_host(volumesFromProvider[volume])
    host = monitorserver.get_hosts(hosts=[volume],
                                   resource='volumes',
                                   output=['name'],
                                   filter={'status': '0'},
                                   macros=['macro', 'value'],
                                   triggers=['triggerid', 'name'],
                                   items=['itemid', 'key_', 'value_type'],
                                   groups=['groupsid', 'name'])
    volumesFromMonitorServer[volume] = host[volume]

# Disable deleted volumes on Monitor Server
for volume in {volume for volume in volumesFromMonitorServer
               if volume not in volumesFromProvider}:
    monitorserver.host_disable(volumesFromMonitorServer[volume])
    del volumesFromMonitorServer[volume]

# Gets the attributes from provider
for host in volumesFromMonitorServer:
    volumesFromMonitorServer[host]['user'] = volumesFromProvider[host]['user']
    volumesFromMonitorServer[host]['size'] = volumesFromProvider[host]['size']
    volumesFromMonitorServer[host]['resource'] = volumesFromProvider[host][
                                                                'resource']
    volumesFromMonitorServer[host]['provider'] = volumesFromProvider[host][
                                                                'provider']
    volumesFromMonitorServer[host]['region'] = volumesFromProvider[host][
                                                                'region']
    volumesFromMonitorServer[host]['type'] = volumesFromProvider[host]['type']
    volumesFromMonitorServer[host]['attachment'] = volumesFromProvider[host][
                                                                'attachment']
    if volumesFromProvider[host]['attachment']:
        volumesFromMonitorServer[host]['attachmentinstance'] = (
                        volumesFromProvider[host]['attachment']['instance'])
        volumesFromMonitorServer[host]['attachmentdevice'] = (
                        volumesFromProvider[host]['attachment']['device'])
        volumesFromMonitorServer[host]['attachmenttime'] = volumesFromProvider[
                                                    host]['attachment']['time']
    else:
        volumesFromMonitorServer[host]['attachmentinstance'] = ''
        volumesFromMonitorServer[host]['attachmentdevice'] = ''
        volumesFromMonitorServer[host]['attachmenttime'] = ''
    volumesFromMonitorServer[host]['detachment'] = volumesFromProvider[host][
                                                                'detachment']
    volumesFromMonitorServer[host]['price'] = volumesFromProvider[host][
                                                                'price']
    volumesFromMonitorServer[host]['launchtime'] = volumesFromProvider[host][
                                                                'launchtime']

# Associate the host with its user, provider, region, launchtime, os
# Update price, type, size, attachment, detachment
for volume in volumesFromMonitorServer:
    monitorserver.host_user_association(volumesFromMonitorServer[volume])
    monitorserver.host_provider_association(volumesFromMonitorServer[volume])
    monitorserver.host_region_association(volumesFromMonitorServer[volume])
    monitorserver.host_launchtime_association(volumesFromMonitorServer[volume])
    monitorserver.host_update_type(volumesFromMonitorServer[volume])
    monitorserver.host_update_size(volumesFromMonitorServer[volume])
    monitorserver.host_update_attachment(volumesFromMonitorServer[volume])
    monitorserver.host_update_detachment(volumesFromMonitorServer[volume])
    monitorserver.host_update_price(volumesFromMonitorServer[volume])

# Update volumes history
for volume in [volume for volume in volumesFromMonitorServer
               if volumesFromMonitorServer[volume]['attachment']]:
    # If the volume instance is attached to a host and registered on server
    if (volumesFromMonitorServer[volume]['attachmentinstance']
       in hostsFromMonitorServer):
        monitorserver.volume_update_history(
            volumesFromMonitorServer[volume],
            hostsFromMonitorServer[volumesFromMonitorServer[volume][
                                            'attachmentinstance']])
    elif (volumesFromMonitorServer[volume]['attachmentinstance']
          in stoppedHostFromMonitorServer):
        monitorserver.volume_update_history(
            volumesFromMonitorServer[volume],
            stoppedHostFromMonitorServer[volumesFromMonitorServer[volume][
                                               'attachmentinstance']])
