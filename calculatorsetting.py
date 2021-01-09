import pytz
from datetime import datetime, timezone
import awsapi as aws
import json
import os


home = os.path.dirname(os.path.realpath(__file__))
AVAILABLE_INSTANCES_FILE = home+"/files/availableinstances.json"
UPDATE_AVAILABLE_INSTANCES = 60*60*24*60 # one day
AVAILABLE_INSTANCES = {}
INSTANCES_RESOURCES = {}
INSTANCES_PRICES = {}

def initialize_instances():
    global AVAILABLE_INSTANCES 
    global INSTANCES_PRICES
    global INSTANCES_RESOURCES
    try:
        AVAILABLE_INSTANCES = json.loads((open(AVAILABLE_INSTANCES_FILE, 'r')).read())
        if NOW - AVAILABLE_INSTANCES['timestamp'] > UPDATE_AVAILABLE_INSTANCES:
            AVAILABLE_INSTANCES = {}
            AVAILABLE_INSTANCES['aws'] = aws.get_instance_types()
            (open(AVAILABLE_INSTANCES_FILE, 'w+')).write(json.dumps({
                'timestamp': NOW, 'data': AVAILABLE_INSTANCES}))
        else:
            AVAILABLE_INSTANCES = AVAILABLE_INSTANCES['data']
            for p in AVAILABLE_INSTANCES:
                INSTANCES_RESOURCES[p] = {}
                INSTANCES_PRICES[p] = {}
                for r in AVAILABLE_INSTANCES[p]:
                    INSTANCES_RESOURCES[p][r] = {}
                    INSTANCES_PRICES[p][r] = {}
                    for i in AVAILABLE_INSTANCES[p][r]:
                        INSTANCES_RESOURCES[p][r][i] = {}
                        INSTANCES_PRICES[p][r][i] = {}
                        for a in AVAILABLE_INSTANCES[p][r][i]:
                            if a == 'resources':
                                INSTANCES_RESOURCES[p][r][i] = AVAILABLE_INSTANCES[p][r][i][a]
                            else:
                                INSTANCES_PRICES[p][r][i][a] = AVAILABLE_INSTANCES[p][r][i][a]

    except (FileNotFoundError, json.decoder.JSONDecodeError):
        AVAILABLE_INSTANCES = {}
        AVAILABLE_INSTANCES['aws'] = aws.get_instance_types()
        (open(AVAILABLE_INSTANCES_FILE, 'w+')).write(json.dumps({
            'timestamp': NOW, 'data': AVAILABLE_INSTANCES}))
        AVAILABLE_INSTANCES = AVAILABLE_INSTANCES['data']
        for p in AVAILABLE_INSTANCES:
            INSTANCES_RESOURCES[p] = {}
            INSTANCES_PRICES[p] = {}
            for r in AVAILABLE_INSTANCES[p]:
                INSTANCES_RESOURCES[p][r] = {}
                INSTANCES_PRICES[p][r] = {}
                for i in AVAILABLE_INSTANCES[p][r]:
                    INSTANCES_RESOURCES[p][r][i] = {}
                    INSTANCES_PRICES[p][r][i] = {}
                    for a in AVAILABLE_INSTANCES[p][r][a]:
                        if a == 'resources':
                            INSTANCES_RESOURCES[p][r][i] = AVAILABLE_INSTANCES[p][r][a]
                        else:
                            INSTANCES_PRICES[p][r][i][a] = AVAILABLE_INSTANCES[p][r][a]


def initialize_monitoring():
    global NOW
    global MODE
    global VIRTUALMACHINES_CALCULATION
    global VOLUMES_CALCULATION
    global HEURISTIC_COMPARE
    global HEURISTIC_TYPE
    global virtualmachines
    global volumes
    global AVAILABLE_INSTANCES 
    global INSTANCES_PRICES
    global INSTANCES_RESOURCES
    NOW = int(datetime.timestamp(datetime.utcnow().astimezone(pytz.utc)))
    MODE = 'monitoring'
    VIRTUALMACHINES_CALCULATION = ['equation-1', 'cost']
    VOLUMES_CALCULATION = ['equation-1', 'cost']
    HEURISTIC_COMPARE = 'price'
    HEURISTIC_TYPE = 'cpu'
    initialize_instances()

def initialize_testing():
    global NOW
    global MODE
    global VIRTUALMACHINES_CALCULATION
    global VOLUMES_CALCULATION
    global HEURISTIC_COMPARE
    global HEURISTIC_TYPE
    global virtualmachines
    global volumes
    global AVAILABLE_INSTANCES 
    global INSTANCES_PRICES
    global INSTANCES_RESOURCES
    NOW = int(datetime.utcnow().replace(tzinfo=timezone.utc).timestamp())
    MODE = 'testing'
    VIRTUALMACHINES_CALCULATION = ['cost', 'equation-1', 'equation-2',
                                   'equation-3']
    VOLUMES_CALCULATION = ['cost', 'equation-1']
    HEURISTIC_COMPARE = 'price'
    HEURISTIC_TYPE = 'vcpu'
    initialize_instances()

def initialize_experimenting():
    global NOW
    global MODE
    global VIRTUALMACHINES_CALCULATION
    global VOLUMES_CALCULATION
    global HEURISTIC_COMPARE
    global HEURISTIC_TYPE
    global virtualmachines
    global volumes
    global AVAILABLE_INSTANCES 
    global INSTANCES_PRICES
    global INSTANCES_RESOURCES
    NOW = int(datetime.timestamp(datetime.utcnow().astimezone(pytz.utc)))
    MODE = 'experimenting'
    VIRTUALMACHINES_CALCULATION = ['cost', 'equation-1', 'equation-2',
                                   'equation-3']
    VOLUMES_CALCULATION = ['cost', 'equation-1']
    HEURISTIC_COMPARE = 'price'
    HEURISTIC_TYPE = 'cpu'
    initialize_instances()
