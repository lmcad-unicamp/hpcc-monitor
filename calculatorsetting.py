"""
Authors: William Felipe C. Tavares, Marcio Roberto Miranda Assis, Edson Borin
Copyright Unicamp
"""
import pytz
from datetime import datetime, timezone
import awsapi as aws
import json
import logging
import os
import inspect

home = os.path.dirname(os.path.realpath(__file__))
logger = logging.getLogger(str(inspect.getouterframes(inspect.currentframe()
                                                      )[-1].filename))
#-----------------
# This variable defines the mode which the calculator will execute
# Fell free to define new functions that initializes with different heuristics
# values: experimenting (does not save history, takes actions or sends data do server)
#         testing (does not send data to server or takes actions users, but saves history)
#         monitoring (sends data to server and takes actions and saves history)
MODE = 'monitoring'
#-----------------

#--------------------------BUCKET.PY-----------------------------------
# The DEMANDS dict tells the system the limits tha differ demands for each finality
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

# The THRESHOLDS is the dict that tells the system the thresholds and the actions to be taken
# You can define thresholds and actions for each finality and each demand
# You can also not define thresholds and actions for a bucket, 
# but once you have a threshold, you must define an action 
# The bucket can have accumulative and reset quantification thresholds
# Each one has a thresholds list, which are hours of wastage
# and an actions list, which are the actions taken by the respective threshold
# default: execution-high demand has accumulative quantification 
#               and a threshold at 3 hours of wastage and 'notification' as an action
#               This means that once the VM reaches the wastage in $ related to
#                   3 hours, a notification will be sended
#               For example, if the VM costs $2.00/h, 
#                 3 hours of wastage means 3h*$2.00/h=$6.00
#                 So the user will be notified when the wastage reaches $6.00 
#       execution-high-accumulative: 3 notification
#       execution-low-accumulative: 2 recommendation
#       execution-idle-accumulative: 2 notification
#       execution-idle-reset: 1 intervention
#       server-high-accumulative: 3 notification
#       server-high-reset: 1 recommendation
#       server-low-accumulative: 3 recommendation
#       server-idle-accumulative: 3 recommendation
#       interaction-high-accumulative: 3 notification
#       interaction-high-reset: 1 recommendation
#       interaction-low-accumulative: 3 recommendation
#       interaction-idle-accumulative: 3 recommendation


ACTION_THRESHOLDS = {'execution': {'high': {'accumulative': {
                                        'thresholds': [3], 
                                        'action': ['notification']}},
                            'low': {'accumulative': {
                                        'thresholds': [2], 
                                        'action': ['recommendation']}},
                            'idle': {'accumulative': {
                                        'thresholds': [2], 
                                        'action': ['notification']}, 
                                     'reset': {
                                        'thresholds': [1], 
                                        'action': ['intervention']}}},
            'server':      {'high': {'accumulative': {
                                        'thresholds': [3], 
                                        'action': ['notification']},
                                    'reset': {
                                        'thresholds': [1], 
                                        'action': ['recommendation']}},
                            'low': {'accumulative': {
                                        'thresholds': [3], 
                                        'action': ['recommendation']}},
                            'idle': {'accumulative': {
                                        'thresholds': [3], 
                                        'action': ['recommendation']}}},
            'interaction': {'high': {'accumulative': {
                                        'thresholds': [3], 
                                        'action': ['notification']},
                                     'reset': {
                                        'thresholds': [1], 
                                        'action': ['recommendation']}},
                            'low': {'accumulative': {
                                        'thresholds': [3], 
                                        'action': ['recommendation']}},
                            'idle': {'accumulative': {
                                        'thresholds': [3], 
                                        'action': ['recommendation']}}}
            }
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
            providers = (open(home+'/private/providers', "r")).read().splitlines()
            for p in providers:
                if p == 'aws':
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
        providers = (open(home+'/private/providers', "r")).read().splitlines()
        for p in providers:
            if p == 'aws':
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