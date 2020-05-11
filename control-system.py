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

# Gets instances from providers
instances = aws.get_instances(pricing=True, ignore={
                                            'tags': {'monitorignore':
                                                     ['True', 'true']},
                                            'state': ['terminated',
                                                      'shutting-down']})
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
                                        'id': instance['id']
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

hostsFromMonitorServer = monitorserver.get_hosts(
                                        output=['name'],
                                        filter={'status': '0'},
                                        macros=['macro', 'value'],
                                        templates=['templateid', 'name'],
                                        groups=['groupsid', 'name']
                                        )

# If the instance is stopped, we are not going to handle it here
for host in {host for host in hostsFromMonitorServer
             if host in hostsFromProviderStopped}:
    del hostsFromMonitorServer[host]

# Detect terminated instances and disable it on Monitor Server
for host in {host for host in hostsFromMonitorServer
             if host not in hostsFromProvider}:
    monitorserver.host_disable(hostsFromMonitorServer[host])
    del hostsFromMonitorServer[host]

# Gets the attributes from provider
for host in hostsFromMonitorServer:
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

# Associate the user with the host when the user is registered
for host in hostsFromMonitorServer:
    if host not in hostsFromProviderUserNotRegistered:
        monitorserver.host_user_association(hostsFromMonitorServer[host])

# Associate the host with its provider, region, family, type, launchtime, price
for host in hostsFromMonitorServer:
    monitorserver.host_provider_association(hostsFromMonitorServer[host])
    monitorserver.host_region_association(hostsFromMonitorServer[host])
    monitorserver.host_service_association(hostsFromMonitorServer[host])
    monitorserver.host_update_family(hostsFromMonitorServer[host])
    monitorserver.host_update_type(hostsFromMonitorServer[host])
    monitorserver.host_launchtime_association(hostsFromMonitorServer[host])
    monitorserver.host_update_instance_price(hostsFromMonitorServer[host])
