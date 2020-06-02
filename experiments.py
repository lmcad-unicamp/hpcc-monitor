import logging
import os
import zapi as monitorserver
import heuristics
import calculatorsetting as cs
from wastageapi import HistoryWastage
from pprint import pprint

home = os.path.dirname(os.path.realpath(__file__))

logger = logging.getLogger(str(__file__))
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
formatter = logging.Formatter('[%(asctime)s] - [%(levelname)5s] - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

HISTORY_VIRTUALMACHINES_FILE = home+"/files/history.virtualmachines"
HISTORY_VOLUMES_FILE = home+"/files/history.volumes"
cs.initialize_experimenting()

# Get hosts from Monitor Server
hostsFromMonitorServer = monitorserver.get_hosts(
                                        get={'tags': ['exp3']},
                                        resource='virtualmachines',
                                        output=['name'],
                                        macros=['macro', 'value'],
                                        templates=['templateid', 'name'],
                                        groups=['groupsid', 'name'],
                                        items=['itemid', 'key_',
                                               'delay', 'value_type'],
                                        user=True,
                                        family=True
                                        )

virtualmachines = HistoryWastage(HISTORY_VIRTUALMACHINES_FILE, mode=cs.MODE)

# If the host does not exist anymore, it is deleted
for host in virtualmachines.get_hosts():
    if not [h for h in hostsFromMonitorServer if h == host]:
        virtualmachines.delete_host(host)

# If the host does not have history, it is added
for host in hostsFromMonitorServer:
    if host not in virtualmachines.get_hosts():
        virtualmachines.add_host(host)
        price_timestamp = 0
        virtualmachines.add_host_attribute(host, 'type',
                                           hostsFromMonitorServer[host]['type']
                                           )
    else:
        price_timestamp = virtualmachines.get_price_timestamp(host)
    prices = monitorserver.get_history(host=hostsFromMonitorServer[host],
                                       itemkey='cloud.price',
                                       since=price_timestamp,
                                       till=cs.NOW)
    virtualmachines.set_pricing_history(host, prices)


# For each host, calculate wastage
for host in hostsFromMonitorServer:
    # If the host does not have price, we cannot calculate wastage
    if not virtualmachines.has_price(host):
        logger.error("[CALCULATOR] The host " + host + " does not have price")
        continue
    # In this heuristic, we look at all resources

    heuristics.virtualmachines_statistics(hostsFromMonitorServer[host],
                                          virtualmachines, monitorserver)
    if 'cost' in cs.VIRTUALMACHINES_CALCULATION:
        heuristics.virtualmachine_cost(hostsFromMonitorServer[host],
                                       virtualmachines, monitorserver)
    if 'heuristic-1' in cs.VIRTUALMACHINES_CALCULATION:
        heuristics.virtualmachine_wastage_heuristic1(
                hostsFromMonitorServer[host], virtualmachines, monitorserver)
    if 'heuristic-2' in cs.VIRTUALMACHINES_CALCULATION:
        heuristics.virtualmachine_wastage_heuristic2(
                hostsFromMonitorServer[host], virtualmachines, monitorserver)
    if 'heuristic-3' in cs.VIRTUALMACHINES_CALCULATION:
        heuristics.virtualmachine_wastage_heuristic3(
                hostsFromMonitorServer[host], virtualmachines, monitorserver)
