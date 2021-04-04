import logging
import os
import inspect
import calculatorsetting as cs
import selections
from datetime import datetime
from pprint import pprint

resource_statistics = {'system.cpu.util[all,idle,avg1]': 'cpu',
                       'gpu.idle': 'gpu',
                       'vm.memory.size[pavailable]': 'memory',
                       'volume.space.free': 'storage'}

virtualmachines_equations = {
    'equation-1': {'accelerated':     'system.cpu.util[all,idle,avg1]',
                    'compute':         'system.cpu.util[all,idle,avg1]',
                    'generalpurpose':  'system.cpu.util[all,idle,avg1]',
                    'memory':          'system.cpu.util[all,idle,avg1]',
                    'storage':         'system.cpu.util[all,idle,avg1]'
                    },
    'equation-2': {'accelerated':     ['gpu.idle',
                                        'system.cpu.util[all,idle,avg1]',
                                        'vm.memory.size[pavailable]'],
                    'compute':         ['system.cpu.util[all,idle,avg1]',
                                        'vm.memory.size[pavailable]'],
                    'generalpurpose':  ['system.cpu.util[all,idle,avg1]',
                                        'vm.memory.size[pavailable]'],
                    'memory':          ['system.cpu.util[all,idle,avg1]',
                                        'vm.memory.size[pavailable]'],
                    'storage':         ['system.cpu.util[all,idle,avg1]',
                                        'vm.memory.size[pavailable]']
                    }
}

volumes_equations = {'equation-1': 'volume.space.free'}


home = os.path.dirname(os.path.realpath(__file__))
logger = logging.getLogger(str(inspect.getouterframes(inspect.currentframe()
                                                      )[-1].filename))


# This function calculates the residual, compulsory and arbitrary wastage and cost
def virtualmachine_calculates(host, virtualmachines, monitorserver,
                                utilization, timestamp, value_delay, 
                                bucket, selection):
    # Get the current instance
    current_instance = virtualmachines.find_type(host['id'], timestamp)
    
    # Get the bucket values
    virtualmachines.set_bucket(host['id'], bucket)
    bucket_history = virtualmachines.get_bucket(host['id'], bucket)
    residual_wastage = bucket_history['residual']
    compulsory_wastage = bucket_history['compulsory']
    arbitrary_wastage = bucket_history['arbitrary']
    reset_wastage = bucket_history['reset']

    if current_instance == selection:
        # Calculates residual wastage
        price = virtualmachines.find_price(host['id'], timestamp)
        residual_wastage += (100-utilization) / 100.0 * price * value_delay
        total_cost = price * value_delay
        virtualmachines.set_bucket_wastage(host['id'], bucket, 
                                            'residual', residual_wastage)
        virtualmachines.set_host_cost(host['id'], total_cost)
    else:
        # Calculates compulsory wastage using the selected instance price
        selected_price = cs.INSTANCES_PRICES[host['provider']][host['region']][selection][host['price_infos']]['price']
        current_compulsory_wastage = (100-utilization) / 100.0 * selected_price * value_delay
        compulsory_wastage += current_compulsory_wastage
        virtualmachines.set_bucket_wastage(host['id'], bucket, 
                                            'compulsory', compulsory_wastage)
        # Calculates arbitrary wastage
        current_price = virtualmachines.find_price(host['id'], timestamp)

        current_wastage = (100-utilization) / 100.0 * current_price * value_delay
        arbitrary_wastage += current_wastage - current_compulsory_wastage
        virtualmachines.set_bucket_wastage(host['id'], bucket, 
                                            'arbitrary', arbitrary_wastage)

        total_cost = current_price * value_delay
        # Calculates the reset wastage
        if bucket != virtualmachines.get_bucket_value(host['id']):
            virtualmachines.reset_bucket(host['id'], bucket)
            reset_wastage = 0
        reset_wastage += current_wastage - current_compulsory_wastage
        virtualmachines.set_bucket_wastage(host['id'], bucket, 
                                            'reset', reset_wastage)
        virtualmachines.set_host_cost(host['id'], total_cost)

    # Send to montior server
    if cs.MODE == 'monitoring':
        monitorserver.send_item(host['id'], 'cost', total_cost)
        monitorserver.send_item(host['id'], 'wastage.'+bucket+'.residual', residual_wastage)
        monitorserver.send_item(host['id'], 'wastage.'+bucket+'.compulsory', compulsory_wastage)
        monitorserver.send_item(host['id'], 'wastage.'+bucket+'.arbitrary', arbitrary_wastage)
        monitorserver.send_item(host['id'], 'wastage.'+bucket+'.reset', reset_wastage)
    virtualmachines.update_bucket_infos(host['id'], bucket, timestamp)

    logger.info("[EQUATIONS] The wastage quantification was updated for instance " 
                + host['id'])


def boot_wastage(host, virtualmachines, monitorserver, timestamp, value_delay):
    # Calculate the boot time
    last_time = virtualmachines.get_last_time(host['id'])
    if last_time == 0:
        last_time = int(datetime.timestamp(host['launchtime']))
    boot_time = (timestamp - last_time - value_delay)/3600
    # Get the current price
    current_price = virtualmachines.find_price(host['id'], timestamp)
    # Calculate boot wastage
    boot_wastage = virtualmachines.get_host_boot(host['id']) + current_price * boot_time
    virtualmachines.set_host_boot(host['id'], boot_wastage)
    if cs.MODE == 'monitoring':
        monitorserver.send_item(host['id'], 'wastage.boot', boot_wastage)
    logger.info("[EQUATIONS] The boot wastage quantification was updated for instance " 
                + host['id'])

# This functions get statistics about resources
def virtualmachines_statistics(host, virtualmachines, monitorserver,
                               timelapse=None):
    # Get the statistics history
    statistics_history = virtualmachines.get_host_statistics(host['id'],
                                                        timelapse=timelapse)

    # For each resource
    for item in [r for r in resource_statistics if r in host['items']]:
        resource = resource_statistics[item]
        if resource not in statistics_history:
            statistics_history[resource] = {'amount': 0, 'timestamp': 0,
                                            'max': 0, 'min': 100, 'mean': 0}
        # Get the values of the item since the last value requested till now
        if timelapse:
            values = monitorserver.get_history(host=host, itemkey=item, 
                                        till=timelapse[1], since=timelapse[0])
        else:
            values = monitorserver.get_history(
                            host=host, itemkey=item, till=cs.NOW,
                            since=statistics_history[resource]['timestamp'])

        # If there are new values
        if values:
            for v in values:
                if v['value'] > statistics_history[resource]['max']:
                    statistics_history[resource]['max'] = v['value']
                if v['value'] < statistics_history[resource]['min']:
                    statistics_history[resource]['min'] = v['value']
                statistics_history[resource]['mean'] = (
                    statistics_history[resource]['mean']
                    + (v['value'] - statistics_history[resource]['mean'])
                    / (statistics_history[resource]['amount'] + 1))
                statistics_history[resource]['amount'] += 1
            statistics_history[resource]['time'] = values[-1]['timestamp'] - (values[0]['timestamp'] - 60)
        statistics_history[resource]['timestamp'] = cs.NOW
        virtualmachines.set_host_statistics(host['id'], statistics_history,
                                            timelapse=timelapse)


# This calculates the host total cost and delay boot
def virtualmachine_cost(host, virtualmachines, monitorserver, 
                        timelapse=None):
    # Get launchtime and restartlaunchtime and convert to timestamp
    launchtime = 0
    if 'launchtime' in host:
        launchtime = int(datetime.timestamp(host['launchtime']))
    restartlaunchtime = 0
    if 'restartlaunchtime' in host:
        restartlaunchtime = int(datetime.timestamp(host['restartlaunchtime']))

    # Get cost and boot history
    cost_history = virtualmachines.get_host_cost(host['id'], 
                                                 timelapse=timelapse)
    if not cost_history:
        cost_history = {'total': 0.0, 'timestamp': launchtime}

    boot_history = virtualmachines.get_host_boot(host['id'],
                                                 timelapse=timelapse)
    if not boot_history:
        boot_history = {'wastage': 0.0, 'timestamp': 0, 'values': []}

    # Convert the sample time to hour and seconds
    item = 'system.cpu.util[all,idle,avg1]'
    item_delay = host['items'][item]['delay']
    value_delay = monitorserver.convert_to_hour(item_delay)
    timestamp_difference = int(monitorserver.convert_to_second(item_delay))

    # Get the values of the item since the last value requested till now
    if timelapse:
        values = monitorserver.get_history(host=host, itemkey=item, 
                                        till=timelapse[1], since=timelapse[0])
    else:
        values = monitorserver.get_history(host=host, itemkey=item, till=cs.NOW,
                                           since=cost_history['timestamp'])
    
    # If there are new values
    if values:
        # Calculate the boot wastage
        if cs.MODE == 'monitoring':
            if (boot_history['timestamp'] == 0
            or boot_history['timestamp'] != restartlaunchtime):
                boot_time = (values[0]['timestamp'] - restartlaunchtime
                            - timestamp_difference)
                
                boot_price = virtualmachines.find_price(host['id'],
                                                        restartlaunchtime)
                boot_wastage = (boot_time/timestamp_difference
                                * boot_price * value_delay)
                boot_history['wastage'] += boot_wastage
                boot_history['values'].append(boot_time)
                boot_history['timestamp'] = restartlaunchtime
                virtualmachines.set_host_boot(host['id'], boot_history, 
                                            timelapse=timelapse)

                # Send to montior server
                if cs.MODE == 'monitoring':
                    monitorserver.send_item(host['id'], 'boot',
                                            boot_history['wastage'])
        else:
            boot_value = 0
            if timelapse:
                boot_values = monitorserver.get_history(host=host, itemkey='wastage.boot', 
                                till=timelapse[1], since=timelapse[0])
            else:
                boot_values = monitorserver.get_history(host=host, 
                                    itemkey='wastage.boot', till=cs.NOW, 
                                    since=boot_history['timestamp'])
            for v in boot_values:
                boot_value += v['value']
            boot_history['wastage'] = boot_value
            boot_history['values'] = [v['value'] for v in boot_values]
            boot_history['timestamp'] = [v['timestamp'] for v in boot_values]
            virtualmachines.set_host_boot(host['id'], boot_history, 
                                            timelapse=timelapse)
                
            
        # Calculate the cost of each sample of value, based onf price history
        cost_calculated = 0.0
        for v in values:
            value_price = virtualmachines.find_price(host['id'],
                                                     v['timestamp'])
            cost = (timestamp_difference/timestamp_difference
                    * value_price * value_delay)
            cost_calculated += cost

        # Update cost history
        cost_history['total'] += cost_calculated
        cost_history['timestamp'] = values[-1]['timestamp']
        virtualmachines.set_host_cost(host['id'], cost_history,
                                      timelapse=timelapse)

        # Send to montior server
        if cs.MODE == 'monitoring':
            monitorserver.send_item(host['id'], 'cost', cost_history['total'])

    logger.info("[EQUATIONS] The cost quantification was updated for instance " 
                + host['id'])

# In this equation, each family of instances has a specific item to look
def virtualmachine_wastage_equation1(host, virtualmachines, monitorserver, 
                                      timelapse=None):
    EQUATION = 'equation-1'
    virtualmachines.set_equation(host['id'], EQUATION, timelapse=timelapse)

    launchtime = 0
    if 'launchtime' in host:
        launchtime = int(datetime.timestamp(host['launchtime']))
    # Get the name of the item
    item = virtualmachines_equations[EQUATION][host['family']]
    # Convert the sample time to hour (which is the unit for prices)
    item_delay = host['items'][item]['delay']
    value_delay = monitorserver.convert_to_hour(item_delay)
    # Get the history of this item
    item_history = virtualmachines.get_item_history(host['id'], EQUATION,
                                                    item, timelapse=timelapse)
    # If the item does not have a history
    if not item_history:
        item_history = {'sum': 0.0, 'timestamp': launchtime, 'len': 0}
    # Get the values of the item since the last value requested till now
    if timelapse:
        values = monitorserver.get_history(host=host, itemkey=item, 
                                        till=timelapse[1], since=timelapse[0])
    else:
        values = monitorserver.get_history(host=host, itemkey=item, till=cs.NOW,
                                       since=item_history['timestamp'])

    # If there are new values
    if values:
        # Calculate the wastage of each sample of value
        item_wastage_calculated = 0.0
        for v in values:
            # Find the price of the sample based on price history
            value_price = virtualmachines.find_price(host['id'],
                                                     v['timestamp'])
            # Calculate the wastage
            # In this equation, takes % out of each sample and multiply
            # with the price of the sample time (in hours)
            wastage = v['value'] / 100.0 * value_price * value_delay
            # Add wastage to the user
            virtualmachines.add_user_wastage(host['user'],
                                             wastage, v['timestamp'])
            # This variable stores the wastage calculated in this execution
            item_wastage_calculated += wastage
        # Store the total wastage of this item and the last timestamp
        item_history['sum'] += item_wastage_calculated
        item_history['timestamp'] = values[-1]['timestamp']
        item_history['len'] += len(values)
        virtualmachines.set_item_history(host['id'], EQUATION, item,
                                         item_history, timelapse=timelapse)

        # Get the wastage of the host and sum with the wastage calculated
        host_equation_wastage_calculated = (
                    virtualmachines.get_host_wastage(host['id'], EQUATION,
                                                     timelapse=timelapse))
        host_equation_wastage_calculated += item_wastage_calculated
        virtualmachines.set_host_wastage(host['id'], EQUATION,
                                         host_equation_wastage_calculated,
                                         timelapse=timelapse)

        # Send to montior server
        if cs.MODE == 'monitoring':
            monitorserver.send_item(host['id'], 'wastage',
                                    host_equation_wastage_calculated)


# In this equation, we calculate based on all resources
def virtualmachine_wastage_equation2(host, virtualmachines, monitorserver, 
                                      timelapse=None):
    EQUATION = 'equation-2'
    virtualmachines.set_equation(host['id'], EQUATION, timelapse=timelapse)
    launchtime = 0
    if 'launchtime' in host:
        launchtime = int(datetime.timestamp(host['launchtime']))

    # Get the name of the item
    for item in virtualmachines_equations[EQUATION][host['family']]:
        # Get the history of this item
        item_history = virtualmachines.get_item_history(host['id'],
                                                        EQUATION, item,
                                                        timelapse=timelapse)
        # Convert the sample time to hour (which is the unit for prices)
        item_delay = host['items'][item]['delay']
        value_delay = monitorserver.convert_to_hour(item_delay)
        timestamp_difference = int(monitorserver.convert_to_second(item_delay))
        # If the item does not have a history
        if not item_history:
            item_history = {'sum': 0.0, 'timestamp': launchtime, 'len': 0}
        # Get the values of the item since last value requested till now
        if timelapse:
            values = monitorserver.get_history(host=host, itemkey=item, 
                                        till=timelapse[1], since=timelapse[0])
        else:
            values = monitorserver.get_history(host=host,
                                           itemkey=item, till=cs.NOW,
                                           since=item_history['timestamp'])

        # If there are new values
        if values:
            # Calculate the wastage of each sample of value
            item_wastage_calculated = 0.0
            for v in values:
                # Find the price of the sample based on price history
                value_price = virtualmachines.find_price(host['id'],
                                                         v['timestamp'])
                # Calculate the wastage
                # In this equation, take % out of each sample and multiply
                # with the price of the sample time (in hours)
                wastage = v['value'] / 100.0 * value_price * value_delay
                # Add wastage to the user
                virtualmachines.add_user_wastage(host['user'],
                                                 wastage, v['timestamp'])
                # This variable stores wastage calculated in this execution
                item_wastage_calculated += wastage
            # Store the total wastage of this item and the last timestamp
            item_history['sum'] = (item_history['sum']
                                   + item_wastage_calculated)
            item_history['timestamp'] = values[-1]['timestamp']
            item_history['len'] = len(values)
            virtualmachines.set_item_history(host['id'], EQUATION, item,
                                             item_history, timelapse=timelapse)

            # Get wastage of the host and sum with the wastage calculated
            host_equation_wastage_calculated = (
                            virtualmachines.get_host_wastage(
                                                    host['id'], EQUATION, 
                                                    timelapse=timelapse))
            host_equation_wastage_calculated += item_wastage_calculated
            virtualmachines.set_host_wastage(
                    host['id'], EQUATION, host_equation_wastage_calculated,
                    timelapse=timelapse)

            # Send to montior server
            if cs.MODE == 'monitoring':
                monitorserver.send_item(host, 'wastage',
                                        host_equation_wastage_calculated)


# In this equation, we calculate based on all resources and divide the price
def virtualmachine_wastage_equation3(host, virtualmachines, monitorserver, 
                                      timelapse=None):
    EQUATION = 'equation-3'
    launchtime = 0
    virtualmachines.set_equation(host['id'], EQUATION, timelapse)
    if 'launchtime' in host:
        launchtime = int(datetime.timestamp(host['launchtime']))
    items_len = len(virtualmachines_equations['equation-2'][host['family']])
    # Get the name of the item
    for item in virtualmachines_equations['equation-2'][host['family']]:
        # Get the history of this item
        item_history = virtualmachines.get_item_history(host['id'], EQUATION,
                                                    item, timelapse=timelapse)
        # Convert the sample time to hour (which is the unit for prices)
        item_delay = host['items'][item]['delay']
        value_delay = monitorserver.convert_to_hour(item_delay)
        # If the item does not have a history
        if not item_history:
            item_history = {'sum': 0.0, 'timestamp': launchtime, 'len': 0}
        # Get the values of the item since last value requested till now
        if timelapse:
            values = monitorserver.get_history(host=host, itemkey=item, 
                                        till=timelapse[1], since=timelapse[0])
        else:
            values = monitorserver.get_history(host=host,
                                           itemkey=item, till=cs.NOW,
                                           since=item_history['timestamp'])

        # If there are new values
        if values:
            # Calculate the wastage of each sample of value
            item_wastage_calculated = 0.0
            for v in values:
                # Find the price of the sample based on price history
                value_price = virtualmachines.find_price(host['id'],
                                                         v['timestamp'])
                # Calculate the wastage
                # In this equation, take % out of each sample and multiply
                # with the price of the sample time (in hours)
                wastage = (v['value'] / 100.0
                           * value_price/items_len * value_delay)
                # Add wastage to the user
                virtualmachines.add_user_wastage(host['user'],
                                                 wastage, v['timestamp'])
                # This variable stores wastage calculated in this execution
                item_wastage_calculated += wastage
            # Store the total wastage of this item and the last timestamp
            item_history['sum'] = (item_history['sum']
                                   + item_wastage_calculated)
            item_history['timestamp'] = values[-1]['timestamp']
            item_history['len'] = len(values)
            virtualmachines.set_item_history(host['id'], EQUATION, item,
                                             item_history, timelapse=timelapse)

            # Get wastage of the host and sum with the wastage calculated
            host_equation_wastage_calculated = (
                            virtualmachines.get_host_wastage(
                                                        host['id'], EQUATION,
                                                        timelapse=timelapse))
            host_equation_wastage_calculated += item_wastage_calculated
            virtualmachines.set_host_wastage(
                    host['id'], EQUATION, host_equation_wastage_calculated,
                    timelapse=timelapse)

            # Send to montior server
            if cs.MODE == 'monitoring':
                monitorserver.send_item(host['id'], 'wastage',
                                        host_equation_wastage_calculated)

# Get the wastage of a specific resource
def virtualmachine_wastage_resource(host, virtualmachines, monitorserver, 
                                    item, timelapse=None):
    # Convert the sample time to hour (which is the unit for prices)
    item_delay = host['items'][item]['delay']
    value_delay = monitorserver.convert_to_hour(item_delay)
    # Get the values of the item since the last value requested till now
    if timelapse:
        values = monitorserver.get_history(host=host, itemkey=item, 
                                        till=timelapse[1], since=timelapse[0])
    else:
        values = monitorserver.get_history(host=host, itemkey=item, till=cs.NOW,
                                            since=0)
    item_values = {'wastage': [], 'utilization': []}
    # If there are new values
    if values:
        # Calculate the wastage of each sample of value
        item_wastage_calculated = 0.0
        for v in values:
            # Find the price of the sample based on price history
            value_price = virtualmachines.find_price(host['id'],
                                                     v['timestamp'])
            # Calculate the wastage
            # In this equation, takes % out of each sample and multiply
            # with the price of the sample time (in hours)
            wastage = v['value'] / 100.0 * value_price * value_delay
            # This variable stores the wastage calculated in this execution
            item_wastage_calculated += wastage
            item_values['wastage'].append(item_wastage_calculated)
            item_values['utilization'].append(100-v['value'])
    return item_values

# This calculates the volume total cost
def volume_cost(host, volumes, monitorserver):
    # Get launchtime and restartlaunchtime and convert to timestamp
    launchtime = 0
    if 'launchtime' in host:
        launchtime = int(datetime.timestamp(host['launchtime']))

    # Get cost and boot history
    cost_history = volumes.get_host_cost(host['id'])
    if not cost_history:
        cost_history = {'total': 0.0, 'timestamp': launchtime}
    last_timestamp = cost_history['timestamp']

    # Calculate the cost of each sample of value, based onf price history
    cost_calculated = 0.0
    value_prices = volumes.find_prices(host['id'], last_timestamp, cs.NOW)
    i_price = 1
    while last_timestamp < cs.NOW:
        if i_price < len(value_prices):
            time_lapse = value_prices[i_price][1]
            last_timestamp = value_prices[i_price][1]
        else:
            time_lapse = cs.NOW - last_timestamp
            last_timestamp = cs.NOW
        cost = value_prices[i_price-1][0] * 0.00027777777 * time_lapse
        cost_calculated += cost
        i_price = i_price + 1

    # Update cost history
    cost_history['total'] += cost_calculated
    cost_history['timestamp'] = cs.NOW
    volumes.set_host_cost(host['id'], cost_history)

    # Send to montior server
    if cs.MODE == 'monitoring':
        monitorserver.send_item(host['id'], 'cost', cost_history['total'])


# In this equation, we calculate the wastage based on free space
def volume_wastage_equation1(host, volumes, monitorserver):
    HEURISTIC = 'equation-1'
    launchtime = 0
    if 'launchtime' in host:
        launchtime = int(datetime.timestamp(host['launchtime']))
    volumes.set_equation(host['id'], HEURISTIC)
    # We set the delay for 1 minute, but the equation handles any period
    # of time between samples
    item_delay = '1m'
    value_delay = monitorserver.convert_to_hour(item_delay)
    timestamp_difference = int(monitorserver.convert_to_second(item_delay))
    # Get the name of the item
    item = volumes_equations[HEURISTIC]
    # Get the history of this item
    item_history = volumes.get_item_history(host['id'], HEURISTIC, item)
    # If the item does not have a history
    if not item_history:
        item_history = {'sum': 0.0, 'timestamp': launchtime,
                        'lastvalue': 100.0}
    # Get the values of the item since the last value requested till now
    values = monitorserver.get_history(host=host, itemkey=item, till=cs.NOW,
                                       since=item_history['timestamp'])

    last_timestamp = item_history['timestamp']
    last_value = item_history['lastvalue']
    # If there are new values
    item_wastage_calculated = 0.0
    time_lapse_wastage = 0.0
    if values:
        # Calculate the wastage of each sample of value
        for v in values:
            # If a time lapse has occur, we calculate the wastage of this
            # period based on last value gathered
            if v['timestamp'] - last_timestamp > timestamp_difference:
                value_prices = volumes.find_prices(host['id'], last_timestamp,
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
            value_price = volumes.find_price(host['id'], v['timestamp'])
            # Calculate the wastage
            wastage = v['value'] / 100.0 * value_price * value_delay * time
            # New last value and last timestamp
            last_value = v['value']
            last_timestamp = v['timestamp']
            # Add wastage to the user
            volumes.add_user_wastage(host['user'], wastage, last_timestamp)
            item_wastage_calculated += wastage

    # If there is no recent value, we compute the last wastage
    if cs.NOW - last_timestamp > timestamp_difference:
        value_prices = volumes.find_prices(host['id'], last_timestamp, cs.NOW)
        i_price = 1
        # For each price, we compute the wastage
        while last_timestamp < cs.NOW:
            if i_price < len(value_prices):
                time_lapse = (value_prices[i_price][1]
                              - last_timestamp)
                last_timestamp = value_prices[i_price][1]
            else:
                time_lapse = cs.NOW - last_timestamp
                last_timestamp = cs.NOW
            wastage = (time_lapse/timestamp_difference
                       * last_value/100.0 * value_prices[i_price-1][0]
                       * value_delay)
            time_lapse_wastage += wastage
            i_price = i_price + 1
            # Add wastage to the user
            volumes.add_user_wastage(host['user'],
                                     wastage, last_timestamp)
        last_timestamp = cs.NOW

    # If new wastage has been calculated
    total_wastage = item_wastage_calculated + time_lapse_wastage
    if total_wastage:
        # Store the new wastage
        item_history['sum'] = item_history['sum'] + total_wastage
        item_history['timestamp'] = last_timestamp
        item_history['lastvalue'] = last_value
        volumes.set_item_history(host['id'], HEURISTIC, item, item_history)
        # Get the wastage of the host and sum with the wastage calculated
        host_equation_wastage_calculated = volumes.get_host_wastage(
                                                        host['id'], HEURISTIC)
        host_equation_wastage_calculated += total_wastage
        volumes.set_host_wastage(host['id'], HEURISTIC,
                                 host_equation_wastage_calculated)
        # Send to montior server
        if cs.MODE == 'monitoring':
            monitorserver.send_item(host['id'], 'wastage',
                                    host_equation_wastage_calculated)
