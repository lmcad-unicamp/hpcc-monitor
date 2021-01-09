import logging
import os
import inspect
import calculatorsetting as cs
import zapi as monitorserver
from datetime import datetime
from pprint import pprint
import awsapi as aws
import json
import math

RESOURCES = {
    'vcpu': 'system.cpu.util[all,user,avg1]',
    'gpu': 'gpu.utilization',
    'memory': 'vm.memory.size[pused]'
}

home = os.path.dirname(os.path.realpath(__file__))
logger = logging.getLogger(str(inspect.getouterframes(inspect.currentframe()
                                                      )[-1].filename))

# This function removes the instances that do not satisfy 
# the demand of each resource from the available instances
def filter(host, virtualmachines, resources_amounts, current_instance, timestamp):
    instances_resources = cs.INSTANCES_RESOURCES[host['provider']][host['region']]
    # All available instances are candidates
    candidates = list(instances_resources.keys())
    # For each available instance

    for i in instances_resources:
        # For each resource in this instance
        for r in resources_amounts:
           # If the amount being used is greater than the capacity 
            # in the instance, the it is not more a candidate
            if r in instances_resources[i]:
                if instances_resources[i][r] < resources_amounts[r]:
                    candidates.remove(i)
                    break
            else:
                if resources_amounts[r] != 0:
                    candidates.remove(i)
                    break
    return candidates

# This function returns the vCPU amount available 
# that are between two values of vCPU amount desired 
def get_search_space(host, instances, vcpu_min, vcpu_max):
    instances_resources = cs.INSTANCES_RESOURCES[host['provider']][host['region']]
    # Get all vCPU amounts available
    vcpu_sizes = []
    for i in instances:
        if instances_resources[i]['vcpu'] not in vcpu_sizes:
            vcpu_sizes.append(instances_resources[i]['vcpu'])
    print(vcpu_sizes)
    # For each vCPU amount available
    search_list = []
    for vcpu in sorted(vcpu_sizes):
        # If it is between the desired amounts, adds it to the list
        if vcpu_min <= vcpu and vcpu <= vcpu_max:
            search_list.append(vcpu)
        # If the size is equal or greater than the maximum desired, 
        # stops the search
        if vcpu >= vcpu_max:
            # If the list is empty, than add the current amount
            if not search_list:
                search_list.append(vcpu)
            break
    
    # If the list is still empty, than adds the maximum available amount
    if not search_list:
        search_list.append(max(vcpu_sizes))

    return search_list
                
# This function is the base for the selection heuristics
def selection_base(host, virtualmachines, filtered_instances, current_instance, 
                    timestamp, vcpu_min, vcpu_max, compare):
    instances_resources = cs.INSTANCES_RESOURCES[host['provider']][host['region']]
    instances_prices = cs.INSTANCES_PRICES[host['provider']][host['region']]
    print(vcpu_min, vcpu_max)
    # Get the search space
    search_space = get_search_space(host, filtered_instances, vcpu_min, vcpu_max)
    print(search_space)
    # Find the cheapest one
    for vcpu in sorted(search_space, reverse=True):
        # Get the instances with the current vCPU amount
        candidates = []
        for i in filtered_instances:
            if vcpu == instances_resources[i]['vcpu']:
                candidates.append(i)
        print(candidates)
        
        # Get the cheapest instance in this set
        cheapest_type = ''
        cheapest_price = float('inf')
        for i in candidates:
            if instances_prices[i][host['price_infos']][compare] < cheapest_price:
                cheapest_type = i
                cheapest_price = instances_prices[i][host['price_infos']][compare]

        # If it is the same type, return
        if cheapest_type == current_instance:
            return current_instance, True

        # If it is cheaper than the current, return
        if cheapest_price < instances_prices[current_instance][host['price_infos']][compare]:
            return cheapest_type, True
    # If there are no cheaper instance, return
    return current_instance, False


# This heuristic uses the vCPU amount that is being used as the desired amount
def vcpu_heuristic(host, virtualmachines, filtered_instances, 
                 resources_utilizations, timestamp, compare):
    instances_resources = cs.INSTANCES_RESOURCES[host['provider']][host['region']]
    # Get the current instance
    current_instance = virtualmachines.find_type(host['id'], timestamp)
    # Calculates the vCPU amount that is being used
    vcpu_size = math.ceil(resources_utilizations['vcpu']*instances_resources[current_instance]['vcpu']/100.0)
    if vcpu_size == 0: vcpu_size = 1
    vcpu_min = vcpu_size
    vcpu_max = vcpu_size
    # Selects an instance
    selected, found = selection_base(host, virtualmachines, filtered_instances, 
                                     current_instance, timestamp, 
                                     vcpu_min, vcpu_max, compare)
    return selected, found

# This heuristic uses the double o the vCPU amount that is being used 
# as the desired amount
def cpu_heuristic(host, virtualmachines, filtered_instances, 
                 resources_utilizations, timestamp, compare):
    instances_resources = cs.INSTANCES_RESOURCES[host['provider']][host['region']]
    # Get the current instance
    current_instance = virtualmachines.find_type(host['id'], timestamp)
    # Calculates the vCPU amount that is being used
    vcpu_size = math.ceil(resources_utilizations['vcpu']*instances_resources[current_instance]['vcpu']/100.0)
    if vcpu_size == 0: vcpu_size = 1
    vcpu_min = 2*vcpu_size
    vcpu_max = 2*vcpu_size
    # Selects an instance
    selected, found = selection_base(host, virtualmachines, filtered_instances, 
                                     current_instance, timestamp, 
                                     vcpu_min, vcpu_max, compare)
    return selected, found

# This heuristic tries the cpu_heuristic and if it fails 
# then tries vcpu_heuristic
def both_heuristic(host, virtualmachines, filtered_instances, 
                 resources_utilizations, timestamp, compare):
    selected, found = vcpu_heuristic(host, virtualmachines, filtered_instances, 
                                     resources_utilizations, 
                                     timestamp, compare)
    if not found:
        selected, found = cpu_heuristic(host, virtualmachines, filtered_instances,
                                        resources_utilizations, 
                                        timestamp, compare)
    return selected, found

# This heuristic decreases the vCPU amount desired from the double to the same 
# as the vCPU amount that is being used
def top_down_heuristic(host, virtualmachines, filtered_instances, 
                 resources_utilizations, timestamp, compare):
    instances_resources = cs.INSTANCES_RESOURCES[host['provider']][host['region']]
    # Get the current instance
    current_instance = virtualmachines.find_type(host['id'], timestamp)
    # Calculates the vCPU amount that is being used
    vcpu_size = math.ceil(resources_utilizations['vcpu']*instances_resources[current_instance]['vcpu']/100.0)
    if vcpu_size == 0: vcpu_size = 1
    vcpu_min = vcpu_size
    vcpu_max = 2*vcpu_size
    # Selects an instance
    selected, found = selection_base(host, virtualmachines, filtered_instances, 
                                     current_instance, timestamp, 
                                     vcpu_min, vcpu_max, compare)
    return selected, found

# Selects the heuristic
def virtualmachine_selection(host, virtualmachines, utilization, 
                                timestamp, compare, heuristic):
    if host['provider'] == 'aws':
        host['price_infos'] = aws.get_instance_infos(host['region'], host['id'])
    else:
        return

    # Get the last utilization of the resources
    instances_resources = cs.INSTANCES_RESOURCES[host['provider']][host['region']]
    current_instance = virtualmachines.find_type(host['id'], timestamp)
    resources_utilizations = {}
    resources_amounts = {}
    for r in instances_resources[current_instance]:
        # Get the utilization in the specific timestamp
        item = RESOURCES[r]
        values = monitorserver.get_history(host=host, itemkey=item, 
                                        since=timestamp-1, limit=1)
        if values:
            resources_utilizations[r] = values[0]['value'] # Calculate the amount of the resource that is being used
            if r in ['vcpu', 'gpu', 'memory']:
                resources_amounts[r] = math.ceil(resources_utilizations[r]*instances_resources[current_instance][r]/100.0)

    if 'vcpu' not in resources_utilizations:
        logger.error("[SELECTION] The instance " + host['id'] + " does not have"
                    + " vCPU utilization")
        return current_instance

    # Filter the candidates based on all resources
    filtered_instances = filter(host, virtualmachines, resources_amounts, current_instance, timestamp)


    if heuristic == 'vcpu':
        selection, found = vcpu_heuristic(host, virtualmachines, filtered_instances, 
                                resources_utilizations, timestamp, compare)
    if heuristic == 'cpu':
        selection, found = cpu_heuristic(host, virtualmachines, filtered_instances, 
                                resources_utilizations, timestamp, compare)
    if heuristic == 'both':
        selection, found = both_heuristic(host, virtualmachines, filtered_instances, 
                                resources_utilizations, timestamp, compare)
    if heuristic == 'topdown':
        selection, found = top_down_heuristic(host, virtualmachines, filtered_instances, 
                                resources_utilizations, timestamp, compare)
    logger.info("[SELECTION] The selection using heuristic " + heuristic + "-" +
                compare + " for instance " + host['id'] + " was " + selection)
    return selection