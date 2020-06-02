import calculatorsetting as cs
from datetime import datetime
from pprint import pprint

resource_statistics = {'system.cpu.util[all,idle,avg1]': 'cpu',
                       'gpu.idle': 'gpu',
                       'vm.memory.size[pavailable]': 'memory',
                       'volume.space.free': 'storage'}

virtualmachines_heuristics = {
    'heuristic-1': {'accelerated':     'gpu.idle',
                    'compute':         'system.cpu.util[all,idle,avg1]',
                    'generalpurpose':  'system.cpu.util[all,idle,avg1]',
                    'memory':          'vm.memory.size[pavailable]',
                    'storage':         'system.cpu.util[all,idle,avg1]'
                    },
    'heuristic-2': {'accelerated':     ['gpu.idle',
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

volumes_heuristics = {'heuristic-1': 'volume.space.free'}


# This functions get statistics about resources
def virtualmachines_statistics(host, virtualmachines, monitorserver):
    # Get the statistics history
    statistics_history = virtualmachines.get_host_statistics(host['id'])

    # For each resource
    for item in [r for r in resource_statistics if r in host['items']]:
        resource = resource_statistics[item]
        if resource not in statistics_history:
            statistics_history[resource] = {'amount': 0, 'timestamp': 0,
                                            'max': 0, 'min': 100, 'mean': 0}
        # Get the values of the item since the last value requested till now
        values = monitorserver.get_history(
                            host=host, itemkey=item, till=cs.NOW,
                            since=statistics_history[resource]['timestamp'])

        # If there is new values
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
        statistics_history[resource]['timestamp'] = cs.NOW


# This calculates the host total cost and delay boot
def virtualmachine_cost(host, virtualmachines, monitorserver):
    # Get launchtime and restartlaunchtime and convert to timestamp
    launchtime = 0
    if 'launchtime' in host:
        launchtime = int(datetime.timestamp(host['launchtime']))
    restartlaunchtime = 0
    if 'restartlaunchtime' in host:
        restartlaunchtime = int(datetime.timestamp(host['restartlaunchtime']))

    # Get cost and boot history
    cost_history = virtualmachines.get_host_cost(host['id'])
    if not cost_history:
        cost_history = {'total': 0.0, 'timestamp': launchtime}

    boot_history = virtualmachines.get_host_boot(host['id'])
    if not boot_history:
        boot_history = {'wastage': 0.0, 'timestamp': 0, 'values': []}

    # Convert the sample time to hour and seconds
    item = 'system.cpu.util[all,idle,avg1]'
    item_delay = host['items'][item]['delay']
    value_delay = monitorserver.convert_to_hour(item_delay)
    timestamp_difference = int(monitorserver.convert_to_second(item_delay))

    # Get the values of the item since the last value requested till now
    values = monitorserver.get_history(host=host, itemkey=item, till=cs.NOW,
                                       since=cost_history['timestamp'])
    # If there is new values
    if values:
        # Calculate the boot wastage
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
            virtualmachines.set_host_boot(host['id'], boot_history)

            # Send to montior server
            if cs.MODE == 'monitoring':
                monitorserver.send_item(host['id'], 'boot',
                                        boot_history['wastage'])

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
        virtualmachines.set_host_cost(host['id'], cost_history)

        # Send to montior server
        if cs.MODE == 'monitoring':
            monitorserver.send_item(host['id'], 'cost', cost_history['total'])


# In this heuristic, each family of instances has a specific item to look
def virtualmachine_wastage_heuristic1(host, virtualmachines, monitorserver):
    HEURISTIC = 'heuristic-1'
    virtualmachines.set_heuristic(host['id'], HEURISTIC)

    launchtime = 0
    if 'launchtime' in host:
        launchtime = int(datetime.timestamp(host['launchtime']))
    # Get the name of the item
    item = virtualmachines_heuristics[HEURISTIC][host['family']]
    # Convert the sample time to hour (which is the unit for prices)
    item_delay = host['items'][item]['delay']
    value_delay = monitorserver.convert_to_hour(item_delay)
    # Get the history of this item
    item_history = virtualmachines.get_item_history(host['id'], HEURISTIC,
                                                    item)
    # If the item does not have a history
    if not item_history:
        item_history = {'sum': 0.0, 'timestamp': launchtime, 'len': 0}
    # Get the values of the item since the last value requested till now
    values = monitorserver.get_history(host=host, itemkey=item, till=cs.NOW,
                                       since=item_history['timestamp'])

    # If there is new values
    if values:
        # Calculate the wastage of each sample of value
        item_wastage_calculated = 0.0
        for v in values:
            # Find the price of the sample based on price history
            value_price = virtualmachines.find_price(host['id'],
                                                     v['timestamp'])
            # Calculate the wastage
            # In this heuristic, takes % out of each sample and multiply
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
        virtualmachines.set_item_history(host['id'], HEURISTIC, item,
                                         item_history)

        # Get the wastage of the host and sum with the wastage calculated
        host_heuristic_wastage_calculated = (
                    virtualmachines.get_host_wastage(host['id'], HEURISTIC))
        host_heuristic_wastage_calculated += item_wastage_calculated
        virtualmachines.set_host_wastage(host['id'], HEURISTIC,
                                         host_heuristic_wastage_calculated)

        # Send to montior server
        if cs.MODE == 'monitoring':
            monitorserver.send_item(host['id'], 'wastage',
                                    host_heuristic_wastage_calculated)


# In this heuristic, we calculate based on all resources
def virtualmachine_wastage_heuristic2(host, virtualmachines, monitorserver):
    HEURISTIC = 'heuristic-2'
    virtualmachines.set_heuristic(host['id'], HEURISTIC)
    launchtime = 0
    if 'launchtime' in host:
        launchtime = int(datetime.timestamp(host['launchtime']))

    # Get the name of the item
    for item in virtualmachines_heuristics[HEURISTIC][host['family']]:
        # Get the history of this item
        item_history = virtualmachines.get_item_history(host['id'],
                                                        HEURISTIC, item)
        # Convert the sample time to hour (which is the unit for prices)
        item_delay = host['items'][item]['delay']
        value_delay = monitorserver.convert_to_hour(item_delay)
        timestamp_difference = int(monitorserver.convert_to_second(item_delay))
        # If the item does not have a history
        if not item_history:
            item_history = {'sum': 0.0, 'timestamp': launchtime, 'len': 0}
        # Get the values of the item since last value requested till now
        values = monitorserver.get_history(host=host,
                                           itemkey=item, till=cs.NOW,
                                           since=item_history['timestamp'])

        # If there is new values
        if values:
            # Calculate the wastage of each sample of value
            item_wastage_calculated = 0.0
            for v in values:
                # Find the price of the sample based on price history
                value_price = virtualmachines.find_price(host['id'],
                                                         v['timestamp'])
                # Calculate the wastage
                # In this heuristic, take % out of each sample and multiply
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
            virtualmachines.set_item_history(host['id'], HEURISTIC, item,
                                             item_history)

            # Get wastage of the host and sum with the wastage calculated
            host_heuristic_wastage_calculated = (
                            virtualmachines.get_host_wastage(host['id'],
                                                             HEURISTIC))
            host_heuristic_wastage_calculated += item_wastage_calculated
            virtualmachines.set_host_wastage(
                    host['id'], HEURISTIC, host_heuristic_wastage_calculated)

            # Send to montior server
            if cs.MODE == 'monitoring':
                monitorserver.send_item(host, 'wastage',
                                        host_heuristic_wastage_calculated)


# In this heuristic, we calculate based on all resources and divide the price
def virtualmachine_wastage_heuristic3(host, virtualmachines, monitorserver):
    HEURISTIC = 'heuristic-3'
    launchtime = 0
    virtualmachines.set_heuristic(host['id'], HEURISTIC)
    if 'launchtime' in host:
        launchtime = int(datetime.timestamp(host['launchtime']))
    items_len = len(virtualmachines_heuristics['heuristic-2'][host['family']])
    # Get the name of the item
    for item in virtualmachines_heuristics['heuristic-2'][host['family']]:
        # Get the history of this item
        item_history = virtualmachines.get_item_history(host['id'], HEURISTIC,
                                                        item)
        # Convert the sample time to hour (which is the unit for prices)
        item_delay = host['items'][item]['delay']
        value_delay = monitorserver.convert_to_hour(item_delay)
        # If the item does not have a history
        if not item_history:
            item_history = {'sum': 0.0, 'timestamp': launchtime, 'len': 0}
        # Get the values of the item since last value requested till now
        values = monitorserver.get_history(host=host,
                                           itemkey=item, till=cs.NOW,
                                           since=item_history['timestamp'])

        # If there is new values
        if values:
            # Calculate the wastage of each sample of value
            item_wastage_calculated = 0.0
            for v in values:
                # Find the price of the sample based on price history
                value_price = virtualmachines.find_price(host['id'],
                                                         v['timestamp'])
                # Calculate the wastage
                # In this heuristic, take % out of each sample and multiply
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
            virtualmachines.set_item_history(host['id'], HEURISTIC, item,
                                             item_history)

            # Get wastage of the host and sum with the wastage calculated
            host_heuristic_wastage_calculated = (
                            virtualmachines.get_host_wastage(host['id'],
                                                             HEURISTIC))
            host_heuristic_wastage_calculated += item_wastage_calculated
            virtualmachines.set_host_wastage(
                    host['id'], HEURISTIC, host_heuristic_wastage_calculated)

            # Send to montior server
            if cs.MODE == 'monitoring':
                monitorserver.send_item(host['id'], 'wastage',
                                        host_heuristic_wastage_calculated)


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


# In this heuristic, we calculate the wastage based on free space
def volume_wastage_heuristic1(host, volumes, monitorserver):
    HEURISTIC = 'heuristic-1'
    launchtime = 0
    if 'launchtime' in host:
        launchtime = int(datetime.timestamp(host['launchtime']))
    volumes.set_heuristic(host['id'], HEURISTIC)
    # We set the delay for 1 minute, but the heuristic handles any periond
    # of time between samples
    item_delay = '1m'
    value_delay = monitorserver.convert_to_hour(item_delay)
    timestamp_difference = int(monitorserver.convert_to_second(item_delay))
    # Get the name of the item
    item = volumes_heuristics[HEURISTIC]
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
    # If there is new values
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
        host_heuristic_wastage_calculated = volumes.get_host_wastage(
                                                        host['id'], HEURISTIC)
        host_heuristic_wastage_calculated += total_wastage
        volumes.set_host_wastage(host['id'], HEURISTIC,
                                 host_heuristic_wastage_calculated)
        # Send to montior server
        if cs.MODE == 'monitoring':
            monitorserver.send_item(host['id'], 'wastage',
                                    host_heuristic_wastage_calculated)
