import logging
import os
import zapi as monitorserver
import pytz
from wastageapi import HistoryWastage
from datetime import datetime
from sendemail import quotaexceeded_email
from pprint import pprint

HEURISTIC = 'heuristic-1'
MODE = 'executing'

heuristics_keys = {'heuristic-1': {'accelerated':     'wastage.gpu.util',
                                   'compute':         'wastage.cpu.util',
                                   'generalpurpose':  'system.cpu.util'
                                                      + '[all,idle,avg1]',
                                   'memory':          'wastage.memory.util',
                                   'storage':         'wastage.cpu.util',
                                   'volumes':         'volume.space.free'
                                   }
                   }

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

HISTORY_VIRTUALMACHINES_FILE = home+"/files/history.virtualmachines"
HISTORY_VOLUMES_FILE = home+"/files/history.volumes"
NOW = int(datetime.timestamp(datetime.utcnow().astimezone(pytz.utc)))


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
                                        family=True
                                        )

virtualmachines = HistoryWastage(HISTORY_VIRTUALMACHINES_FILE, mode=MODE)

# If the host does not exist anymore, it is deleted
for host in virtualmachines.get_hosts():
    if not [h for h in hostsFromMonitorServer if h == host]:
        virtualmachines.delete_host(host)

# If the host does not have history, it is added
for host in hostsFromMonitorServer:
    if host not in virtualmachines.get_hosts():
        virtualmachines.add_host(host)
        price_timestamp = 0
    else:
        price_timestamp = virtualmachines.get_price_timestamp(host)
    prices = monitorserver.get_history(host=hostsFromMonitorServer[host],
                                       itemkey='cloud.price',
                                       since=price_timestamp,
                                       till=NOW)
    virtualmachines.set_pricing_history(host, prices)


# For each host, calculate wastage
for host in hostsFromMonitorServer:
    # If the host does not have price, we cannot calculate wastage
    if not virtualmachines.has_price(host):
        logger.error("[CALCULATOR] The host " + host + " does not have price")
        continue
    launchtime = 0
    if 'launchtime' in hostsFromMonitorServer[host]:
        launchtime = int(datetime.timestamp(hostsFromMonitorServer[
                                            host]['launchtime']))

    virtualmachines.set_heuristic(host, HEURISTIC)

    # In this heuristic, each family of instances has a specific item to look
    if HEURISTIC == 'heuristic-1':
        # Get the name of the item
        item = heuristics_keys['heuristic-1'][hostsFromMonitorServer[host][
                                                                    'family']]
        # Get the history of this item
        item_history = virtualmachines.get_item_history(host, HEURISTIC, item)
        # Convert the sample time to hour (which is the unit for prices)
        item_delay = hostsFromMonitorServer[host]['items'][item]['delay']
        value_delay = monitorserver.convert_to_hour(item_delay)
        timestamp_difference = int(monitorserver.convert_to_second(item_delay))
        # If the item does not have a history
        if not item_history:
            item_history = {'sum': 0.0, 'timestamp': launchtime}
        # Get the values of the item since the last value requested till now
        values = monitorserver.get_history(host=hostsFromMonitorServer[host],
                                           itemkey=item, till=NOW,
                                           since=item_history['timestamp'])

        # If there is new values
        if values:
            # Calculate the wastage of each sample of value
            item_wastage_calculated = 0.0
            for v in values:
                # Find the price of the sample based on price history
                value_price = virtualmachines.find_price(host, v['timestamp'])
                # Calculate the wastage
                # In this heuristic, takes % out of each sample and multiply
                # with the price of the sample time (in hours)
                wastage = v['value'] / 100.0 * value_price * value_delay
                # Add wastage to the user
                virtualmachines.add_user_wastage(hostsFromMonitorServer[host][
                                                 'user'],
                                                 wastage, v['timestamp'])
                # This variable stores the wastage calculated in this execution
                item_wastage_calculated += wastage
            # Store the total wastage of this item and the last timestamp
            item_history['sum'] = item_history['sum'] + item_wastage_calculated
            item_history['timestamp'] = values[-1]['timestamp']
            virtualmachines.set_item_history(host, HEURISTIC, item,
                                             item_history)

            # Get the wastage of the host and sum with the wastage calculated
            host_heuristic_wastage_calculated = (
                            virtualmachines.get_host_wastage(host, HEURISTIC))
            host_heuristic_wastage_calculated += item_wastage_calculated
            virtualmachines.set_host_wastage(host, HEURISTIC,
                                             host_heuristic_wastage_calculated)

            # Send to montior server
            if MODE == 'executing':
                monitorserver.send_item(host, 'wastage',
                                        host_heuristic_wastage_calculated)

# Get volumes from Monitor Server
hostsFromMonitorServer = monitorserver.get_hosts(
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

volumes = HistoryWastage(HISTORY_VOLUMES_FILE, mode=MODE)

# If the host does not exist anymore, it is deleted
for host in volumes.get_hosts():
    if not [h for h in hostsFromMonitorServer if h == host]:
        volumes.delete_host(host)

# If the host does not have history, it is added
for host in hostsFromMonitorServer:
    if host not in volumes.get_hosts():
        volumes.add_host(host)
        price_timestamp = 0
    else:
        price_timestamp = volumes.get_price_timestamp(host)
    prices = monitorserver.get_history(host=hostsFromMonitorServer[host],
                                       itemkey='cloud.price',
                                       since=price_timestamp,
                                       till=NOW)
    volumes.set_pricing_history(host, prices)

# For each host, calculate wastage
for host in hostsFromMonitorServer:
    # If the host does not have price, we cannot calculate wastage
    if not volumes.has_price(host):
        logger.error("[CALCULATOR] The host " + host + " does not have price")
        continue
    launchtime = 0
    if 'launchtime' in hostsFromMonitorServer[host]:
        launchtime = int(datetime.timestamp(hostsFromMonitorServer[
                                            host]['launchtime']))

    volumes.set_heuristic(host, HEURISTIC)
    # In this heuristic, each family of instances has a specific item to look
    if HEURISTIC == 'heuristic-1':
        # Get the name of the item and first timestamp
        item = heuristics_keys['heuristic-1']['volumes']
        # We set the delay for 1 minute, but the heuristic handles any periond
        # of time between samples
        item_delay = '1m'
        value_delay = monitorserver.convert_to_hour(item_delay)
        timestamp_difference = int(monitorserver.convert_to_second(item_delay))
        # Get the history of this item
        item_history = volumes.get_item_history(host, HEURISTIC, item)
        # If the item does not have a history
        if not item_history:
            item_history = {'sum': 0.0, 'timestamp': launchtime,
                            'lastvalue': 100.0}
        # Get the values of the item since the last value requested till now
        values = monitorserver.get_history(host=hostsFromMonitorServer[host],
                                           itemkey=item,
                                           since=item_history['timestamp'],
                                           till=NOW)
        last_timestamp = item_history['timestamp']
        last_value = item_history['lastvalue']
        # If there is new values
        item_wastage_calculated = 0.0
        time_lapse_wastage = 0.0
        if values:
            # Calculate the wastage of each sample of value
            for v in values:
                # If a time lapse has occur, we calculate the wastage of this
                # period based on last value gathered
                if v['timestamp'] - last_timestamp > timestamp_difference:
                    value_prices = volumes.find_prices(host, last_timestamp,
                                                       v['timestamp']
                                                       - timestamp_difference)
                    i_price = 1
                    while last_timestamp < (v['timestamp']
                                            - timestamp_difference):
                        if i_price < len(value_prices):
                            time_lapse = (value_prices[i_price][1]
                                          - last_timestamp)
                            last_timestamp = value_prices[i_price][1]
                        else:
                            time_lapse = (v['timestamp'] - timestamp_difference
                                          - last_timestamp)
                            last_timestamp = (v['timestamp']
                                              - timestamp_difference)
                        wastage = (last_value/100.0
                                   * value_prices[i_price-1][0] * value_delay
                                   * time_lapse/timestamp_difference)
                        time_lapse_wastage += wastage
                        i_price = i_price + 1
                # Take the time in minutes
                time = ((v['timestamp'] - last_timestamp)
                        / timestamp_difference)
                # Take the price of the timestamp
                value_price = volumes.find_price(host, v['timestamp'])
                # Calculate the wastage
                wastage = v['value'] / 100.0 * value_price * value_delay * time
                # New last value and last timestamp
                last_value = v['value']
                last_timestamp = v['timestamp']
                # Add wastage to the user
                volumes.add_user_wastage(hostsFromMonitorServer[host]['user'],
                                         wastage, v['timestamp'])
                item_wastage_calculated += wastage

        # If there is no recent value, we compute the last wastage
        if NOW - last_timestamp > timestamp_difference:
            value_prices = volumes.find_prices(host, last_timestamp,
                                               NOW)
            i_price = 1
            # For each price, we compute the wastage
            while last_timestamp < NOW:
                if i_price < len(value_prices):
                    time_lapse = (value_prices[i_price][1]
                                  - last_timestamp)
                    last_timestamp = value_prices[i_price][1]
                else:
                    time_lapse = NOW - last_timestamp
                    last_timestamp = NOW
                wastage = (time_lapse/timestamp_difference
                           * last_value/100.0 * value_prices[i_price-1][0]
                           * value_delay)
                time_lapse_wastage += wastage
                i_price = i_price + 1
                # Add wastage to the user
                volumes.add_user_wastage(hostsFromMonitorServer[host]['user'],
                                         wastage, v['timestamp'])
            last_timestamp = NOW

        # If new wastage has been calculated
        total_wastage = item_wastage_calculated + time_lapse_wastage
        if total_wastage:
            # Store the new wastage
            item_history['sum'] = item_history['sum'] + total_wastage
            item_history['timestamp'] = last_timestamp
            item_history['lastvalue'] = last_value
            volumes.set_item_history(host, HEURISTIC, item, item_history)
            # Get the wastage of the host and sum with the wastage calculated
            host_heuristic_wastage_calculated = volumes.get_host_wastage(
                                                            host, HEURISTIC)
            host_heuristic_wastage_calculated += total_wastage
            volumes.set_host_wastage(host, HEURISTIC,
                                     host_heuristic_wastage_calculated)
            # Send to montior server
            if MODE == 'executing':
                monitorserver.send_item(host, 'wastage',
                                        host_heuristic_wastage_calculated)

if MODE == 'executing':
    # Check if quota of the user has been exceeded
    for user in virtualmachines.get_users():
        if (virtualmachines.get_user_attribute(user, 'permonth')
           >= virtualmachines.get_user_attribute(user, 'quota')):
            try:
                emails = monitorserver.get_admins_email()
                emails.append(monitorserver.get_user_email(
                                        hostsFromMonitorServer[host]['user']))
                quotaexceeded_email(emails,
                                    virtualmachines.get_user_attribute(
                                                            user, 'quota'),
                                    virtualmachines.get_user_attribute(
                                                            user, 'permonth'))
            except monitorserver.NotFoudException as e:
                logger.error("[CALCULATOR] Quota exceeded " + user
                             + ". Could not send email to admins and user "
                             + user + ": "
                             + str(e))
            else:
                logger.info("[CALCULATOR] Quota exceeded. Sending email "
                            + "to admins and user "
                            + virtualmachines.get_user_attribute(
                                                            user, 'permonth'))
