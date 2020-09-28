import logging
import os
import zapi as monitorserver
import heuristics
import calculatorsetting as cs
from wastageapi import HistoryWastage
from pprint import pprint
import matplotlib.pyplot as plt
KEY = 'experimento'
VALUE = "exp5-2-nas-bt"
TIMES = 'experiments/exp5/timelapse'
timelapses = {}
GRAPHS_DIR = 'experiments/exp5/graphs-bt-2'

#gawk '/ParamountItEnd/ {SUM+=$10} END {print SUM/NR, NR, SUM}'
if os.path.isfile(TIMES):
    f = open(TIMES, 'r')
    line = f.readline().strip('\n')
    while line:
        instance = line
        timelapses[instance] = []
        line = f.readline().strip('\n')
        while 'i-' not in line and len(line) != 0:
            line2 = f.readline().strip('\n')
            timelapses[instance].append([int(line), int(line2)])
            line = f.readline().strip('\n')
try:
    os.mkdir(GRAPHS_DIR)
except:
    pass
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

def utilization_graph(host, timelapse=None):
    statistics_history = {}
    cost = []
    if timelapse:
        for v in monitorserver.get_history(host=host, itemkey='cost', till=timelapse[1],
                                        since=timelapse[0]):
            cost.append(v['value'])
    else:
        for v in monitorserver.get_history(host=host, itemkey='cost', till=cs.NOW,
                                    since=0):
            cost.append(v['value'])
    for item in [r for r in heuristics.resource_statistics if r in host['items']]:
        resource = heuristics.resource_statistics[item]
        statistics_history[resource] = heuristics.virtualmachine_wastage_resource(
                                    host, virtualmachines, monitorserver, item, timelapse=timelapse)
    fig = plt.figure()
    ax = fig.add_subplot()
    peak = []
    for r in statistics_history:
        duration = len(statistics_history[r]['utilization'])
        plt.plot(statistics_history[r]['utilization'], label=r)
        peak.append(max(statistics_history[r]['utilization']))
    ax.hlines(10, 0, duration, linestyles='dashed', color='#db1807')
    ax.hlines(80, 0, duration, linestyles='dashed', color='#15ab07')
    plt.margins(0)
    plt.ylim(0, 101)
    plt.ylabel('utilization [%]')
    plt.xlabel('time [min]')
    plt.legend()
    plt.yticks([0,100]+peak)
    plt.title('Utilization of ' + host['type'])
    if timelapse:
        plt.savefig(GRAPHS_DIR+'/'+host['type']+'.utilization.timelapse'+str(timelapse)+'.png', dpi=60)
    else:
        plt.savefig(GRAPHS_DIR+'/'+host['type']+'.utilization.png', dpi=60)
    #plt.show()
    plt.clf()
    
    max_wastage = 0
    for r in statistics_history:
        plt.plot(statistics_history[r]['wastage'], label=r)
        if max_wastage < statistics_history[r]['wastage'][-1]:
            max_wastage = statistics_history[r]['wastage'][-1]
    plt.plot(cost, label='cost')
    plt.hlines(1, 0, duration, linestyles=(0, (5, 10)), color='#ffd024')
    plt.hlines(2, 0, duration, linestyles=(0, (5, 10)), color='#ff9c24')
    plt.hlines(5, 0, duration, linestyles=(0, (5, 10)), color='#ff7824')
    plt.hlines(10, 0, duration, linestyles=(0, (5, 10)), color='#ff4924')
    plt.hlines(20, 0, duration, linestyles=(0, (5, 10)), color='#ff2424')
    plt.ylabel('price [USD]')
    plt.xlabel('time [min]')
    plt.legend()
    plt.margins(0)
    plt.yticks([0,1,2,5,10]+[cost[-1]]+[statistics_history[r]['wastage'][-1] for r in statistics_history])
    plt.ylim(top=cost[-1])
    plt.title('Wastage of ' + host['type'])
    if timelapse:
        plt.savefig(GRAPHS_DIR+'/'+host['type']+'.wastage.timelapse'+str(timelapse)+'.png', dpi=60)
    else:
        plt.savefig(GRAPHS_DIR+'/'+host['type']+'.wastage.png', dpi=60)
    #plt.show()
    plt.clf()


# Get hosts from Monitor Server
hostsFromMonitorServer = monitorserver.get_hosts(
    get={'tags': {KEY: VALUE}},
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

    utilization_graph(hostsFromMonitorServer[host])

    if host in timelapses:
        for timelapse in timelapses[host]:
            virtualmachines.add_timelapse(host, timelapse)
            utilization_graph(hostsFromMonitorServer[host], timelapse=timelapse)
            heuristics.virtualmachines_statistics(
                hostsFromMonitorServer[host], virtualmachines, monitorserver,
                timelapse=timelapse)
            if 'cost' in cs.VIRTUALMACHINES_CALCULATION:
                heuristics.virtualmachine_cost(hostsFromMonitorServer[host],
                                               virtualmachines, monitorserver,
                                               timelapse=timelapse)
            if 'heuristic-1' in cs.VIRTUALMACHINES_CALCULATION:
                heuristics.virtualmachine_wastage_heuristic1(
                    hostsFromMonitorServer[host], virtualmachines, monitorserver,
                    timelapse=timelapse)
            if 'heuristic-2' in cs.VIRTUALMACHINES_CALCULATION:
                heuristics.virtualmachine_wastage_heuristic2(
                    hostsFromMonitorServer[host], virtualmachines, monitorserver,
                    timelapse=timelapse)
            if 'heuristic-3' in cs.VIRTUALMACHINES_CALCULATION:
                heuristics.virtualmachine_wastage_heuristic3(
                    hostsFromMonitorServer[host], virtualmachines, monitorserver,
                    timelapse=timelapse)
