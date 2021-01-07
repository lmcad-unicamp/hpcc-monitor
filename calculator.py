import logging
import os
import zapi as monitorserver
import calculatorsetting as cs
import equations
import selections
import buckets
import actions
from wastageapi import HistoryWastage
from sendemail import quotaexceeded_email
from pprint import pprint
home = os.path.dirname(os.path.realpath(__file__))

logger = logging.getLogger(str(__file__))
logger.setLevel(logging.INFO)
fh = logging.FileHandler(home+"/log/calculator.log")
ch = logging.StreamHandler()
formatter = logging.Formatter('[%(asctime)s] - [%(levelname)5s] - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(ch)

HISTORY_VIRTUALMACHINES_FILE = home+"/files/history.virtualmachines.json"
HISTORY_VOLUMES_FILE = home+"/files/history.volumes.json"

cs.initialize_testing()
virtualmachines = HistoryWastage(HISTORY_VIRTUALMACHINES_FILE, mode=cs.MODE)

# Get hosts from Monitor Server
hostsFromMonitorServer = monitorserver.get_hosts(
                                        resource='virtualmachines',
                                        output=['name'],
                                        filter={'status': '0'},
                                        macros=['macro', 'value'],
                                        templates=['templateid', 'name'],
                                        groups=['groupsid', 'name'],
                                        items=['itemid', 'key_',
                                               'delay', 'value_type'],
                                        user=True,
                                        family=True)


# If the host does not exist anymore, it is deleted
for host in virtualmachines.get_hosts():
    if not [h for h in hostsFromMonitorServer if h == host]:
        virtualmachines.delete_host(host)

# If the host does not have history, it is initialized
for host in hostsFromMonitorServer:
    if host not in virtualmachines.get_hosts():
        virtualmachines.add_host(host)
        price_timestamp = 0
        type_timestamp = 0
    else:
        price_timestamp = virtualmachines.get_price_timestamp(host)
        type_timestamp = virtualmachines.get_type_timestamp(host)
    prices = monitorserver.get_history(host=hostsFromMonitorServer[host],
                                       itemkey='cloud.price',
                                       since=price_timestamp,
                                       till=cs.NOW)
    virtualmachines.set_pricing_history(host, prices)
    types = monitorserver.get_history(host=hostsFromMonitorServer[host],
                                       itemkey='cloud.type',
                                       since=type_timestamp,
                                       till=cs.NOW)
    virtualmachines.set_type_history(host, types)

# For each host, analyze the wastage
for host in hostsFromMonitorServer:
    # If the host does not have price, we cannot calculate wastage
    if not virtualmachines.has_price(host):
        logger.error("[CALCULATOR] The host " + host + " does not have price")
        continue

    # Categorizes the virtual machine
    buckets.virtualmachine_category(hostsFromMonitorServer[host],
                                       virtualmachines, monitorserver)
    item = 'system.cpu.util[all,user,avg1]'
    values = monitorserver.get_history(host=hostsFromMonitorServer[host], 
                                    itemkey=item, till=cs.NOW,
                            since=virtualmachines.get_bucket_timestamp(host))
    if values:  
        demands = []
        for v in values:
            # Convert the sample time to hour (which is the unit for prices)
            item_delay = hostsFromMonitorServer[host]['items'][item]['delay']
            value_delay = monitorserver.convert_to_hour(item_delay)
            timestamp = v['timestamp']
            # Calculate boot wastage
            if timestamp - virtualmachines.get_last_time(host) >= 2*value_delay:
                equations.boot_wastage(hostsFromMonitorServer[host], virtualmachines, 
                                        monitorserver, timestamp, value_delay)
            
            # Selects an instance that optimizes the cost and maintains the performance
            selection, found = selections.virtualmachine_selection(
                                                hostsFromMonitorServer[host],
                                                virtualmachines,
                                                float(v['value']), 
                                                v['timestamp'], 
                                                cs.HEURISTIC_COMPARE, 
                                                cs.HEURISTIC_TYPE)
            # Get the bucket
            finality = virtualmachines.find_finality(host, timestamp)
            demand = virtualmachines.find_demand(host, timestamp)
            bucket = finality + '-' + demand
            # Calculates the wastages
            equations.virtualmachine_calculates(hostsFromMonitorServer[host],
                                                virtualmachines, monitorserver,
                                                float(v['value']), timestamp, 
                                                value_delay, bucket, selection)

            # Takes an action
            actions.virtualmachine_action(hostsFromMonitorServer[host], 
                                virtualmachines, timestamp, bucket, selection)
            virtualmachines.set_last_time(host, timestamp)
            print(host, selection, bucket)
            print("\n\n\n")
    continue
    

    if 'cost' in cs.VIRTUALMACHINES_CALCULATION:
        equations.virtualmachine_cost(hostsFromMonitorServer[host],
                                       virtualmachines, monitorserver)
    if 'equation-1' in cs.VIRTUALMACHINES_CALCULATION:
        equations.virtualmachine_wastage_equation1(
                hostsFromMonitorServer[host], virtualmachines, monitorserver)
    if 'equation-2' in cs.VIRTUALMACHINES_CALCULATION:
        equations.virtualmachine_wastage_equation2(
                hostsFromMonitorServer[host], virtualmachines, monitorserver)
    if 'equation-3' in cs.VIRTUALMACHINES_CALCULATION:
        equations.virtualmachine_wastage_equation3(
                hostsFromMonitorServer[host], virtualmachines, monitorserver)
exit(1)
# --------------------------------------------------------------------------
volumes = HistoryWastage(HISTORY_VOLUMES_FILE, mode=cs.MODE)
# Get volumes from Monitor Server
volumesFromMonitorServer = monitorserver.get_hosts(
                                        resource='volumes',
                                        output=['name'],
                                        filter={'status': '0'},
                                        macros=['macro', 'value'],
                                        templates=['templateid', 'name'],
                                        groups=['groupsid', 'name'],
                                        items=['itemid', 'key_',
                                               'delay', 'value_type'],
                                        user=True,
                                        family=True
                                        )

# If the host does not exist anymore, it is deleted
for host in volumes.get_hosts():
    if not [h for h in volumesFromMonitorServer if h == host]:
        volumes.delete_host(host)

# If the host does not have history, it is added
for host in volumesFromMonitorServer:
    if host not in volumes.get_hosts():
        volumes.add_host(host)
        price_timestamp = 0
    else:
        price_timestamp = volumes.get_price_timestamp(host)
    prices = monitorserver.get_history(host=volumesFromMonitorServer[host],
                                       itemkey='cloud.price',
                                       since=price_timestamp,
                                       till=cs.NOW)
    volumes.set_pricing_history(host, prices)

# For each host, calculate wastage
for host in volumesFromMonitorServer:
    # If the host does not have price, we cannot calculate wastage
    if not volumes.has_price(host):
        logger.error("[CALCULATOR] The host " + host + " does not have price")
        continue

    if 'cost' in cs.VOLUMES_CALCULATION:
        equations.volume_cost(volumesFromMonitorServer[host],
                               volumes, monitorserver)
    if 'equation-1' in cs.VOLUMES_CALCULATION:
        equations.volume_wastage_equation1(volumesFromMonitorServer[host],
                                             volumes, monitorserver)

# -----------------------------------------------------------------------------

# Check if quota of the user has been exceeded
for user in virtualmachines.get_users():
    quota = virtualmachines.get_user_attribute(user, 'quota')
    permonth = virtualmachines.get_user_attribute(user, 'permonth')
    if permonth >= quota:
        try:
            emails = monitorserver.get_admins_email()
            emails.append(monitorserver.get_user_email(user))
            if cs.MODE == 'executing':
                quotaexceeded_email(emails, quota, permonth)
        except monitorserver.NotFoudException as e:
            logger.error("[CALCULATOR] Quota exceeded " + user
                         + ". Could not send email to admins and user "
                         + user + ": "
                         + str(e))
        else:
            logger.info("[CALCULATOR] Quota exceeded. Sending email "
                        + "to admins and user " + user
                        + ". Quota: " + str(quota)
                        + " Usage: " + str(permonth))
