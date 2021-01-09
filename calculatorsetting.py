import pytz
from datetime import datetime, timezone
import awsapi as aws
import json
import os

home = os.path.dirname(os.path.realpath(__file__))

#-----------------
# This variable defines the mode which the calculator will execute
# Fell free to define new functions that initializes with different heuristics
# values: experimenting (does not save history, takes actions or sends data do server)
#         testing (does not send data to server or takes actions users, but saves history)
#         monitoring (sends data to server and takes actions and saves history)
MODE = 'testing'
#-----------------

#--------------------------BUCKET.PY-----------------------------------
# The DEMANDS dict tells the sytem the limits tha differ demands for each finality
# Feel free to define new finalities and new demands
# To define a new finality, you should edit selections.py so the system can categorize a VM
# To define a new demand, you just need to add it to the DEMANDS dict. It must be reversed sorted.
# default: execution, with 'high' demand higher than 90% utilization
#                     with 'low' demand higher than 10% utilization
#                     with 'idle' demand higher than 0% utilization
#           server, 'high' 80%, 'low' 10%, 'idle' 0%
#           interaction, 'high' 70%, 'low' 10%, 'idle' 0%

BUCKET_DEMANDS = {'execution': {'high': 90, 'low': 10, 'idle': 0},
                'server': {'high': 80, 'low': 10, 'idle': 0},
                'interaction': {'high': 70, 'low': 10, 'idle': 0}}

# The DEMAND_METRIC dict tells the system the metric to use to categorize the demand
# default: all finalities uses the vCPU utilization

BUCKET_DEMAND_METRIC = {'execution': 'system.cpu.util[all,user,avg1]',
                        'server': 'system.cpu.util[all,user,avg1]',
                        'interaction': 'system.cpu.util[all,user,avg1]'}
#--------------------------------------------------------------------------

#--------------------------SELECTIONS.PY-----------------------------------
# The RESOURCES tells the system the resources used to filter the instances.
# Each resource has a metric, which is the metric to use to gatter the data utilization
# and a unit, which is the unit of the utilization
# Our system only uses percentage as unit
# default: vcpu, gpu and memory, both with percentage unit and respective Zabbix item

SELECTIONS_RESOURCES = {
    'vcpu': {'metric': 'system.cpu.util[all,user,avg1]', 'unit': 'percentage'},
    'gpu': {'metric': 'gpu.utilization', 'unit': 'percentage'},
    'memory': {'metric': 'vm.memory.size[pused]', 'unit': 'percentage'}
}
#--------------------------------------------------------------------------


#--------------------------ACTIONS.PY----------------------------------
# This variable defines the time IN SECONDS between actions of the same bucket 
# for the same instance
# default: 10 minutes
ACTION_TIME_BETWEEN_ACTIONS = 600

# This variable defines the amount of actions that the sytem takes for a bucket
# for a instance before notifing the admins
# default: 5 times
ACTION_AMOUNT_OF_ACTIONS_TAKEN = 5
#----------------------------------------------------------------------


#----------------------------------------------------------------------
# This variable defines the time IN SECONDS to update the available instances 
# and their prices
# This information is used by selections.py to select a instance
# default: one day
UPDATE_AVAILABLE_INSTANCES = 60*60*24

# This variable defines the metric which the sytem uses to quantify wastage
# default: vCPU utilization
WASTAGE_QUANTIFICATION_METRIC = 'system.cpu.util[all,user,avg1]'
#----------------------------------------------------------------------

AVAILABLE_INSTANCES_FILE = home+"/files/availableinstances.json"
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
    global VOLUMES_CALCULATION
    global HEURISTIC_COMPARE
    global HEURISTIC_TYPE
    global AVAILABLE_INSTANCES 
    global INSTANCES_PRICES
    global INSTANCES_RESOURCES
    global BUCKET_DEMANDS
    global BUCKET_DEMAND_METRIC
    NOW = int(datetime.timestamp(datetime.utcnow().astimezone(pytz.utc)))
    MODE = 'monitoring'
    VOLUMES_CALCULATION = ['equation-1', 'cost']
    HEURISTIC_COMPARE = 'price'
    HEURISTIC_TYPE = 'cpu'
    initialize_instances()

def initialize_testing():
    global NOW
    global MODE
    global VOLUMES_CALCULATION
    global HEURISTIC_COMPARE
    global HEURISTIC_TYPE
    global AVAILABLE_INSTANCES 
    global INSTANCES_PRICES
    global INSTANCES_RESOURCES
    global BUCKET_DEMANDS
    global BUCKET_DEMAND_METRIC
    NOW = int(datetime.utcnow().replace(tzinfo=timezone.utc).timestamp())
    MODE = 'testing'
    VOLUMES_CALCULATION = ['cost', 'equation-1']
    HEURISTIC_COMPARE = 'price'
    HEURISTIC_TYPE = 'vcpu'
    initialize_instances()

def initialize_experimenting():
    global NOW
    global MODE
    global VOLUMES_CALCULATION
    global HEURISTIC_COMPARE
    global HEURISTIC_TYPE
    global AVAILABLE_INSTANCES 
    global INSTANCES_PRICES
    global INSTANCES_RESOURCES
    global BUCKET_DEMANDS
    global BUCKET_DEMAND_METRIC
    NOW = int(datetime.timestamp(datetime.utcnow().astimezone(pytz.utc)))
    MODE = 'experimenting'
    VOLUMES_CALCULATION = ['cost', 'equation-1']
    HEURISTIC_COMPARE = 'price'
    HEURISTIC_TYPE = 'cpu'
    initialize_instances()


def calculator_init():
    if MODE == 'testing':
        initialize_testing()
    elif MODE == 'monitoring':
        initialize_monitoring()
    elif MODE == 'experimenting':
        initialize_experimenting()
    else:
        logger.error("NO MODE DETECTED")