import logging
import os
import zapi as monitorserver
import pytz
from wastageapi import HistoryWastage
from datetime import datetime
from sendemail import quotaexceeded_email
from pprint import pprint

HEURISTIC = 'heuristic-1'

heuristics_keys = {'heuristic-1': {'accelerated':     'wastage.gpu.util',
                                   'compute':         'wastage.cpu.util',
                                   'generalpurpose':  'system.cpu.util'
                                                      + '[all,idle,avg1]',
                                   'memory':          'wastage.memory.util',
                                   'storage':         'wastage.cpu.util'
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

HISTORY_ITEMS_FILE = home+"/files/history.items"
NOW = int(datetime.timestamp(datetime.utcnow().astimezone(pytz.utc)))

# Get hosts from Monitor Server
hostsFromMonitorServer = monitorserver.get_hosts(
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

history = HistoryWastage(HISTORY_ITEMS_FILE)

# If the host does not exist anymore, it is deleted
for host in history.get_hosts():
    if not [h for h in hostsFromMonitorServer if h == host]:
        history.delete_host(host)

# If the host does not have history, it is added
# Update the prices
for host in hostsFromMonitorServer:
    if host not in history.get_hosts():
        history.add_host(host)
        price_timestamp = 0
    else:
        price_timestamp = history.get_price_timestamp(host)
    prices = monitorserver.get_history(host=hostsFromMonitorServer[host],
                                       itemkey='cloud.price',
                                       since=price_timestamp,
                                       till=NOW)
    history.set_pricing_history(host, prices)


# For each host, calculate wastage
for host in hostsFromMonitorServer:
    # If the host does not have price, we cannot calculate wastage
    if not history.has_price(host):
        logger.error("[CALCULATOR] The host " + host + " does not have price")
        continue

    history.set_heuristic(host, HEURISTIC)

    # In this heuristic, each family of instances has a specific item to look
    if HEURISTIC == 'heuristic-1':
        # Get the name of the item
        item = heuristics_keys['heuristic-1'][hostsFromMonitorServer[host][
                                                                    'family']]
        # Get the history of this item
        item_history = history.get_item_history(host, HEURISTIC, item)
        # If the item does not have a history
        if not item_history:
            item_history = {'sum': 0.0, 'timestamp': 0}
        # Get the values of the item since the last value requested till now
        values = monitorserver.get_history(
                                        host=hostsFromMonitorServer[host],
                                        itemkey=item,
                                        since=item_history['timestamp'],
                                        till=NOW)
        # If there is new values
        if values:
            # Convert the sample time to hour (which is the unit for prices)
            item_delay = hostsFromMonitorServer[host]['items'][item]['delay']
            value_delay = monitorserver.convert_to_hour(item_delay)

            # Calculate the wastage of each sample of value
            item_wastage_calculated = 0.0
            for v in values:
                # Convert the type of the value(the function returns as string)
                value = monitorserver.convert_value_type(
                    v['value'],
                    hostsFromMonitorServer[host]['items'][item]['value_type'])
                # Find the price of the sample based on price history
                value_price = history.find_price(host, v['timestamp'])
                # Calculate the wastage
                # In this heuristic, takes % out of each sample and multiply
                # with the price of the sample time (in hours)
                wastage = value / 100.0 * value_price * value_delay
                # Add wastage to the user
                history.add_user_wastage(hostsFromMonitorServer[host]['user'],
                                         wastage, v['timestamp'])
                # This variable stores the wastage calculated in this execution
                item_wastage_calculated = item_wastage_calculated + wastage

            # Store the total wastage of this item and the last timestamp
            item_history['sum'] = item_history['sum'] + item_wastage_calculated
            item_history['timestamp'] = values[-1]['timestamp']
            history.set_item_history(host, HEURISTIC, item, item_history)

            # Get the wastage of the host and sum with the wastage calculated
            host__heuristic_wastage_calculated = history.get_host_wastage(
                                                            host, HEURISTIC)
            host__heuristic_wastage_calculated = (
                                        host__heuristic_wastage_calculated
                                        + item_wastage_calculated)
            history.set_host_wastage(host, HEURISTIC,
                                     host__heuristic_wastage_calculated)

            # Send to montior server
            monitorserver.send_item(hostsFromMonitorServer[host], 'wastage',
                                    host__heuristic_wastage_calculated)


# Check if quota of the user has been exceeded
for user in history.get_users():
    if (history.get_user_attribute(user, 'permonth')
       >= history.get_user_attribute(user, 'quota')):
        try:
            emails = monitorserver.get_admins_email()
            emails.append(monitorserver.get_user_email(hostsFromMonitorServer[
                                                       host]['user']))
            quotaexceeded_email(emails,
                                history.get_user_attribute(user, 'quota'),
                                history.get_user_attribute(user, 'permonth'))
        except monitorserver.NotFoudException as e:
            logger.error("[CALCULATOR] Quota exceeded " + user
                         + ". Could not send email to admins and user "
                         + user + ": "
                         + str(e))
        else:
            logger.info("[CALCULATOR] Quota exceeded. Sending email to admins "
                        + "and user "
                        + history.get_user_attribute(user, 'permonth'))
