import pytz
from datetime import datetime

def initialize_monitoring():
    global NOW
    global MODE
    global VIRTUALMACHINES_CALCULATION
    global VOLUMES_CALCULATION
    global virtualmachines
    global volumes
    NOW = int(datetime.timestamp(datetime.utcnow().astimezone(pytz.utc)))
    MODE = 'monitoring'
    VIRTUALMACHINES_CALCULATION = ['heuristic-1']
    VOLUMES_CALCULATION = ['heuristic-1']

def initialize_testing():
    global NOW
    global MODE
    global VIRTUALMACHINES_CALCULATION
    global VOLUMES_CALCULATION
    global virtualmachines
    global volumes
    NOW = int(datetime.timestamp(datetime.utcnow().astimezone(pytz.utc)))
    MODE = 'testing'
    VIRTUALMACHINES_CALCULATION = ['cost', 'heuristic-1', 'heuristic-2',
                                   'heuristic-3']
    VOLUMES_CALCULATION = ['cost', 'heuristic-1']

def initialize_experimenting():
    global NOW
    global MODE
    global VIRTUALMACHINES_CALCULATION
    global VOLUMES_CALCULATION
    global virtualmachines
    global volumes
    NOW = int(datetime.timestamp(datetime.utcnow().astimezone(pytz.utc)))
    MODE = 'experimenting'
    VIRTUALMACHINES_CALCULATION = ['cost', 'heuristic-1', 'heuristic-2',
                                   'heuristic-3']
    VOLUMES_CALCULATION = ['cost', 'heuristic-1']
