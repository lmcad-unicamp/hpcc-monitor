import logging
import os
import inspect
import calculatorsetting as cs
import zapi as monitorserver
from datetime import datetime
from pprint import pprint

DEMANDS = {'execution': {'high': 90, 'low': 10, 'idle': 0},
            'server': {'high': 80, 'low': 10, 'idle': 0},
            'interaction': {'high': 70, 'low': 10, 'idle': 0}}

home = os.path.dirname(os.path.realpath(__file__))
logger = logging.getLogger(str(inspect.getouterframes(inspect.currentframe()
                                                      )[-1].filename))


def virtualmachine_category(host, virtualmachines, monitorserver, 
                             timelapse=None):
    # Get the values of the ssh.connections item since the last value requested till now
    item = 'ssh.connections'
    if timelapse:
        values = monitorserver.get_history(host=host, itemkey=item, 
                                        till=timelapse[1], since=timelapse[0])
    else:
        values = monitorserver.get_history(host=host, itemkey=item,
                        since=virtualmachines.get_finality_last_time(host['id']))


    # Categorize the finality
    finalities = []
    LAST_FANALITY = virtualmachines.get_finality_value(host['id'])

    # The finality is execution
    PREVIOUS_FINALITY = 'execution'

    # If the host has server label, the finality is server
    tags = monitorserver.get_tags(host['id_zabbix']) 
    for t in tags:
        if t['tag'] == 'server' and t['value'].upper() == 'TRUE':
            PREVIOUS_FINALITY = 'server'
            break
    # If there are values from ssh.connection
    if values:
        # For each value
        for v in values:
            FINALITY = PREVIOUS_FINALITY
            # If there is an user connected
            if v['value']:
                FINALITY = 'interaction'
            
            # Add the finality if it is different from the previous
            if FINALITY != LAST_FANALITY:
                val = {}
                val['value'] = FINALITY
                val['timestamp'] = v['timestamp']
                finalities.append(val)
                LAST_FANALITY = FINALITY
    # If there are not values from ssh.connection
    else:
        # If it is different from the last in the history
        if PREVIOUS_FINALITY != LAST_FANALITY:
            val = {}
            val['value'] = PREVIOUS_FINALITY
            val['timestamp'] = cs.NOW
            finalities.append(val)
    virtualmachines.set_finality_history(host['id'], finalities)


    # Define the demand

    # Get the values of the item since the last value requested till now
    item = 'system.cpu.util[all,user,avg1]'
    if timelapse:
        values = monitorserver.get_history(host=host, itemkey=item, 
                                        till=timelapse[1], since=timelapse[0])
    else:
        values = monitorserver.get_history(host=host, itemkey=item, till=cs.NOW,
                        since=virtualmachines.get_demand_last_time(host['id']))
    
    LAST_DEMAND = virtualmachines.get_demand_value(host['id'])
    
    demands = []
    if values:  
        # For each utilization rate
        for v in values:
            # Get the finality in this timestamp
            finality = virtualmachines.find_finality(host['id'], v['timestamp'])
            utilization = float(v['value'])
            # Get the demand categorization based on the utilization
            for d in DEMANDS[finality]:
                if utilization >= DEMANDS[finality][d]:
                    demand = d
                    break
            # Adds the demand to the demand history
            if demand != LAST_DEMAND:
                val = {}
                val['value'] = demand
                val['timestamp'] = v['timestamp']
                demands.append(val)
                LAST_DEMAND = demand
    virtualmachines.set_demand_history(host['id'], demands)
    logger.info("[BUCKET] The finalities and demands for instance " 
                + host['id'] + " were updated")
