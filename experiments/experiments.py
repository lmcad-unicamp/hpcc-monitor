import os
import re
import math
import json
import numpy as np
import scipy.stats
from pprint import pprint

APP = ['BT-1', 'LU-1', 'SP-1', 'FT-1', 'CG-1', 'IS-1',
        'BT-2', 'LU-2', 'SP-2', 'FT-2', 'CG-2', 'IS-2',
        'BT-3', 'LU-3', 'SP-3', 'FT-3', 'CG-3', 'IS-3',
        'EP-1', 'EP-2', 'EP-3']

pricereason_exp = True
price_exp = True
home = os.path.dirname(os.path.realpath(__file__))
EXPERIMENTS_DIR = home + "/results"
EXPERIMENTS_FILE = EXPERIMENTS_DIR + "/" + "exp2.40.json"
if not os.path.exists(EXPERIMENTS_DIR):
    os.makedirs(EXPERIMENTS_DIR)
DIR = {}
for i in APP:
    DIR[i] = {}
    #DIR[i]['experiment4'] = 'limited-threads/4/'+i+'/'
    #DIR[i]['experiment16'] = 'limited-threads/16/'+i+'/'
    DIR[i]['experiments'] = 'unlimited-threads/experiments/'+i+'/'
    DIR[i]['selections'] = 'unlimited-threads/selections/'+i+'/'


INSTANCES = {'r5xlarge' : {'name': 'r5xlarge', 'dotname': 'r5.xlarge', 'subname': 'r5.x', 'vcpu': 4, 'cpu': 2, 'mem': 32, 'price': 0.25},
            'r52xlarge' : {'name': 'r52xlarge', 'dotname': 'r5.2xlarge', 'subname': 'r5.2x', 'vcpu': 8, 'cpu': 4, 'mem': 64, 'price': 0.50},
            'r54xlarge' : {'name': 'r54xlarge', 'dotname': 'r5.4xlarge', 'subname': 'r5.4x', 'vcpu': 16, 'cpu': 8, 'mem': 128, 'price': 1.01},
            'r58xlarge' : {'name': 'r58xlarge', 'dotname': 'r5.8xlarge', 'subname': 'r5.8x', 'vcpu': 32, 'cpu': 16, 'mem': 256, 'price': 2.02},
            'r512xlarge' : {'name': 'r512xlarge', 'dotname': 'r5.12xlarge', 'subname': 'r5.12x', 'vcpu': 48, 'cpu': 24, 'mem': 384, 'price': 3.02},
            'r5axlarge' : {'name': 'r5axlarge', 'dotname': 'r5a.xlarge', 'subname': 'r5a.x', 'vcpu': 4, 'cpu': 2, 'mem': 32, 'price': 0.23},
            'r5a2xlarge' : {'name': 'r5a2xlarge', 'dotname': 'r5a.2xlarge', 'subname': 'r5a.2x', 'vcpu': 8, 'cpu': 4, 'mem': 64, 'price': 0.45},
            'r5a8xlarge' : {'name': 'r5a8xlarge', 'dotname': 'r5a.8xlarge', 'subname': 'r5a.8x', 'vcpu': 32, 'cpu': 16, 'mem': 128, 'price': 0.90},
            'c54xlarge' : {'name': 'c54xlarge', 'dotname': 'c5.4xlarge', 'subname': 'c5.4x', 'vcpu': 16, 'cpu': 8, 'mem': 32, 'price': 0.68},
            'c59xlarge' : {'name': 'c59xlarge', 'dotname': 'c5.9xlarge', 'subname': 'c5.9x', 'vcpu': 36, 'cpu': 18, 'mem': 72, 'price': 1.53},
            'c512xlarge' : {'name': 'c512xlarge', 'dotname': 'c5.12xlarge', 'subname': 'c5.12x', 'vcpu': 48, 'cpu': 24, 'mem': 96, 'price': 2.04},
            'c5a4xlarge' : {'name': 'c5a4xlarge', 'dotname': 'c5a.4xlarge', 'subname': 'c5a.4x', 'vcpu': 16, 'cpu': 8, 'mem': 32, 'price': 0.62},
            'c5a8xlarge' : {'name': 'c5a8xlarge', 'dotname': 'c5a.8xlarge', 'subname': 'c5a.8x', 'vcpu': 32, 'cpu': 16, 'mem': 64, 'price': 1.23},
            'r5n8xlarge' : {'name': 'r5n8xlarge', 'dotname': 'r5n.8xlarge', 'subname': 'r5n.8x', 'vcpu': 32, 'cpu': 16, 'mem': 256, 'price': 2.38},
            'r5n12xlarge' : {'name': 'r5n12xlarge', 'dotname': 'r5n.12xlarge', 'subname': 'r5n.12x', 'vcpu': 48, 'cpu': 24, 'mem': 384, 'price': 3.58},
            'c5n4xlarge' : {'name': 'c5n4xlarge', 'dotname': 'c5n.4xlarge', 'subname': 'c5n.4x', 'vcpu': 16, 'cpu': 8, 'mem': 42, 'price': 0.86},
            'c5n9xlarge' : {'name': 'c5n9xlarge', 'dotname': 'c5n.9xlarge', 'subname': 'c5n.9x', 'vcpu': 36, 'cpu': 18, 'mem': 96, 'price': 1.94},
            'i32xlarge' : {'name': 'i32xlarge', 'dotname': 'i3.2xlarge', 'subname': 'i3.2x', 'vcpu': 8, 'cpu': 4, 'mem': 61, 'price': 0.62},
            'i34xlarge' : {'name': 'i34xlarge', 'dotname': 'i3.4xlarge', 'subname': 'i3.4x', 'vcpu': 16, 'cpu': 8, 'mem': 122, 'price': 1.25},
            't32xlarge' : {'name': 't32xlarge', 'dotname': 't3.2xlarge', 'subname': 't3.2x', 'vcpu': 8, 'cpu': 4, 'mem': 32, 'price': 0.33}
            }


sortedbyvcpu = ['r5axlarge', 'r5xlarge', 't32xlarge', 'r5a2xlarge',
                'r52xlarge', 'i32xlarge', 'c5a4xlarge', 'c54xlarge', 
                'c5n4xlarge', 'r54xlarge', 'i34xlarge', 'r5a8xlarge',
                'c5a8xlarge', 'r58xlarge', 'r5n8xlarge', 'c59xlarge', 
                'c5n9xlarge', 'c512xlarge', 'r512xlarge', 'r5n12xlarge']

heuristic_name = {'vcpu': 'vCPU-', 'cpu': 'core-', 
                'both': 'hybrid-', 'topdown': 'top-down-',
                'vcpu-pricereason': 'vCPU-ppv-', 
                'cpu-pricereason': 'core-ppv-', 
                'both-pricereason': 'hybrid-ppv-', 
                'topdown-pricereason': 'top-down-ppv-'}
EXP = {}
ALL_EXP = {}
BETTER = {}
price_heuristics = {}
price_heuristics['vcpu'] = {}
price_heuristics['cpu'] = {}
price_heuristics['both'] = {}
price_heuristics['topdown'] = {}
pricereason_heuristics = {}
pricereason_heuristics['vcpu-pricereason'] = {}
pricereason_heuristics['cpu-pricereason'] = {}
pricereason_heuristics['both-pricereason'] = {}
pricereason_heuristics['topdown-pricereason'] = {}
heuristics = {}
if price_exp:
    heuristics.update(price_heuristics)
if pricereason_exp:
    heuristics.update(pricereason_heuristics)


INSTANCES_PER_VCPU = {}
for i in INSTANCES:
    if INSTANCES[i]['vcpu'] not in INSTANCES_PER_VCPU:
        INSTANCES_PER_VCPU[INSTANCES[i]['vcpu']] = []
    INSTANCES_PER_VCPU[INSTANCES[i]['vcpu']].append(i)
    INSTANCES[i]['pricereason'] = INSTANCES[i]['price'] / INSTANCES[i]['vcpu']

if __name__ == '__main__':

    def get_searchspace(instances_list, minvcpu, maxvcpu):
        vcpus_available = []
        for vm in INSTANCES:
            if vm in instances_list:
                vcpus_available.append(INSTANCES[vm]['vcpu'])
        minvcpu = int(minvcpu)
        maxvcpu = int(maxvcpu)
        vcpus_list = [] 
        for vcpus in sorted(vcpus_available):
            if vcpus >= minvcpu and vcpus <= maxvcpu: vcpus_list.append(vcpus)
            if vcpus >= maxvcpu: 
                if not vcpus_list:
                    vcpus_list.append(vcpus)
                break
        if not vcpus_list:
            vcpus_list.append(max(vcpus_available))
        return vcpus_list
        
    def get_cheaper(instances, compare_type='price'):
        lowest = float('inf')
        instance = ''
        for i in instances:
            if INSTANCES[i][compare_type] < lowest:
                instance = i
                lowest = INSTANCES[i][compare_type]
        return instance

    def experiment_filter(app):
        new_instances = []
        for i in INSTANCES:
            if i in ALL_EXP[app]:
                new_instances.append(i)
        return new_instances

    def heuristic_algorithm(current, minvcpus, maxvcpus, app, compare_type='price'):
        # Remove from the search space those instances that does not have an experiment executed
        # This is not the filter of other resources
        # this is only to not choose a instance that do not have an execution for this app
        filtered_candidates = experiment_filter(app)
        # Get search space, in this case min and max are the min of vcpus
        searchspace = get_searchspace(filtered_candidates, minvcpus, maxvcpus)
        for s in sorted(searchspace, reverse=True):
            candidates = []
            for i in filtered_candidates:
                if INSTANCES[i]['vcpu'] == s:
                    candidates.append(i)
            # Get the cheaper
            selected = get_cheaper(candidates, compare_type)
            # If the selected is the same as the current
            if selected == current:
                return current, True
            # If the price of the selected is lower than the current
            if INSTANCES[selected][compare_type] < INSTANCES[current][compare_type]:
                return selected, True
        # If no cheaper instance has been found
        return current, False

    def calculate_overheads(h, threads, app, vm, selected):
        if threads not in heuristics[h][app]:
            heuristics[h][app][threads] = {}
        heuristics[h][app][threads][vm] = {}
        heuristic = heuristics[h][app][threads][vm]
        this = EXP[app][threads]

        heuristic['selected'] = {}
        heuristic['selected']['same'] = False
        if selected == vm:
            heuristic['selected']['same'] = True
        heuristic['selected'] = EXP[app][threads][selected] 
        heuristic['current'] = EXP[app][threads][vm] 
        
        heuristic['ovcost'] = this[vm]['cost'] / this[selected]['cost']
        heuristic['ovperf'] = this[vm]['pi'] / this[selected]['pi']

        heuristic['blocal-costovcost'] = this[selected]['cost'] / BETTER[app][threads]['cost']
        heuristic['blocal-costovperf'] = this[selected]['pi'] / BETTER[app][threads]['costpi']
        heuristic['blocal-piovcost'] = this[selected]['cost'] / BETTER[app][threads]['picost']
        heuristic['blocal-piovperf'] = this[selected]['pi'] / BETTER[app][threads]['pi']
        heuristic['bglobal-costovcost'] = this[selected]['cost'] / BETTER[app]['global']['cost']
        heuristic['bglobal-costovperf'] = this[selected]['pi'] / BETTER[app]['global']['costpi']
        heuristic['bglobal-piovcost'] = this[selected]['cost'] / BETTER[app]['global']['picost']
        heuristic['bglobal-piovperf'] = this[selected]['pi'] / BETTER[app]['global']['pi']
    
    def paramount_iteration_lower_than():
        for app in APP:
            for dir in DIR[app]:
                dir = DIR[app][dir]
                if os.path.exists(dir):
                    for file in os.listdir(dir):
                        if file.endswith(".exp"):
                            a = float(os.popen("gawk '/ParamountItEnd/ {NUM+=1} END {print NUM}' "+dir+file).read().rstrip())
                            a = int(a)
                            if a < 40:
                                print(a, app, dir, file)

    paramount_iteration_lower_than()

    for app in APP:
        EXP[app] = {}
        ALL_EXP[app] = []
        BETTER[app] = {}
        for dir in DIR[app]:
            experiment = False 
            if dir[0:10] == 'experiment':
                experiment = True 
            dir = DIR[app][dir]
            if os.path.exists(dir):
                for file in os.listdir(dir):
                    if file.endswith(".exp"):
                        fileattr = file.split('.')
                        instancename = fileattr[0]
                        numthreads = int(fileattr[3])
                        if instancename not in ALL_EXP[app]:
                            ALL_EXP[app].append(instancename)
                        # Get information about the experiment
                        if numthreads not in EXP[app]:
                            EXP[app][numthreads] = {}
                        EXP[app][numthreads][instancename] = {}
                        this = EXP[app][numthreads][instancename]
                        this['threads'] = numthreads
                        pi = float(os.popen("gawk '/ParamountItEnd/ {if (NUM<40) SUM+=$10; NUM+=1;} END {print SUM/40/1000/1000}' "+dir+file).read().rstrip())
                        #pi = float(os.popen("gawk '/ParamountItEnd/ {SUM+=$10} END {print SUM/NR/1000/1000}' "+dir+file).read().rstrip())
                        this['pi'] = pi
                        cost = pi * INSTANCES[instancename]['price'] / 60 / 60
                        this['cost'] = cost
                        this['utilization'] = numthreads / INSTANCES[instancename]['vcpu']
                        this['instance'] = INSTANCES[instancename]
                        this['experiment'] = experiment
                        # Select the better instance in the experiment
                        if numthreads not in BETTER[app]:
                            BETTER[app][numthreads] = {}
                            BETTER[app][numthreads]['pi'] = pi
                            BETTER[app][numthreads]['pii'] = instancename
                            BETTER[app][numthreads]['picost'] = cost
                            BETTER[app][numthreads]['cost'] = cost
                            BETTER[app][numthreads]['costi'] = instancename
                            BETTER[app][numthreads]['costpi'] = pi
                        else:
                            if BETTER[app][numthreads]['pi'] > pi:
                                BETTER[app][numthreads]['pi'] = pi
                                BETTER[app][numthreads]['pii'] = instancename
                                BETTER[app][numthreads]['picost'] = cost
                            if BETTER[app][numthreads]['cost'] > cost:
                                BETTER[app][numthreads]['cost'] = cost
                                BETTER[app][numthreads]['costi'] = instancename
                                BETTER[app][numthreads]['costpi'] = pi
                        
                        # Select the better instance in all executions
                        if 'global' not in BETTER[app]:
                            BETTER[app]['global'] = {}
                            BETTER[app]['global']['pi'] = pi
                            BETTER[app]['global']['pii'] = instancename
                            BETTER[app]['global']['picost'] = cost
                            BETTER[app]['global']['cost'] = cost
                            BETTER[app]['global']['costi'] = instancename
                            BETTER[app]['global']['costpi'] = pi
                        else:
                            if BETTER[app]['global']['pi'] > pi:
                                BETTER[app]['global']['pi'] = pi
                                BETTER[app]['global']['pii'] = instancename
                                BETTER[app]['global']['picost'] = cost
                            if BETTER[app]['global']['cost'] > cost:
                                BETTER[app]['global']['cost'] = cost
                                BETTER[app]['global']['costi'] = instancename
                                BETTER[app]['global']['costpi'] = pi

        if price_exp:
            # vCPU-heuristic
            print("vCPU-heuristic")
            heuristics['vcpu'][app] = {}
            for threads in EXP[app]:
                for vm in EXP[app][threads]:
                    # Get min of vcpus is the amount shown in utilization rate
                    minvcpus = EXP[app][threads][vm]['utilization']*INSTANCES[vm]['vcpu']
                    # Run the heuristic
                    selected, found = heuristic_algorithm(vm, minvcpus, minvcpus, app, compare_type='price')
                    # Calculate the performance and cost overheads
                    calculate_overheads('vcpu', threads, app, vm, selected)

            # CPU-heuristic
            print("CPU-heuristic")
            heuristics['cpu'][app] = {}
            for threads in EXP[app]:
                for vm in EXP[app][threads]:
                    minvcpus = 2*EXP[app][threads][vm]['utilization']*INSTANCES[vm]['vcpu']
                    selected, found = heuristic_algorithm(vm, minvcpus, minvcpus, app, compare_type='price')
                    calculate_overheads('cpu', threads, app, vm, selected)

            # both-heuristic
            print("both-heuristic")
            heuristics['both'][app] = {}
            for threads in EXP[app]:
                for vm in EXP[app][threads]:
                    # Try CPU-heuristic   
                    minvcpus = 2*EXP[app][threads][vm]['utilization']*INSTANCES[vm]['vcpu']
                    selected, found = heuristic_algorithm(vm, minvcpus, minvcpus, app, compare_type='price')
                    # If failed, try vCPU-heuristic
                    if not found:
                        minvcpus = EXP[app][threads][vm]['utilization']*INSTANCES[vm]['vcpu']
                        selected, found = heuristic_algorithm(vm, minvcpus, minvcpus, app, compare_type='price')
                    calculate_overheads('both', threads, app, vm, selected)

            # top-down-heuristic
            print("top-down-heuristic")
            heuristics['topdown'][app] = {}
            for threads in EXP[app]:
                for vm in EXP[app][threads]:
                    # Get min of vcpus is the two times the amount shown in utilization rate
                    minvcpus = EXP[app][threads][vm]['utilization']*INSTANCES[vm]['vcpu']
                    # Get max of vcpus is the two times the amount shown in utilization rate
                    maxvcpus = 2*EXP[app][threads][vm]['utilization']*INSTANCES[vm]['vcpu']
                    
                    selected, found = heuristic_algorithm(vm, minvcpus, maxvcpus, app, compare_type='price')

                    calculate_overheads('topdown', threads, app, vm, selected)

        if pricereason_exp:
            # vCPU-pricereason-heuristic
            print("vCPU-pricereason-heuristic")
            heuristics['vcpu-pricereason'][app] = {}
            for threads in EXP[app]:
                for vm in EXP[app][threads]:
                    minvcpus = EXP[app][threads][vm]['utilization']*INSTANCES[vm]['vcpu']
                    selected, found = heuristic_algorithm(vm, minvcpus, minvcpus, app, compare_type='pricereason')
                    calculate_overheads('vcpu-pricereason', threads, app, vm, selected)
            
            # CPU-pricereason-heuristic
            print("CPU-pricereason-heuristic")
            heuristics['cpu-pricereason'][app] = {}
            for threads in EXP[app]:
                for vm in EXP[app][threads]:
                    minvcpus = 2*EXP[app][threads][vm]['utilization']*INSTANCES[vm]['vcpu']
                    selected, found = heuristic_algorithm(vm, minvcpus, minvcpus, app, compare_type='pricereason')
                    calculate_overheads('cpu-pricereason', threads, app, vm, selected)

            # both-pricereason-heuristic
            print("both-pricereason-heuristic")
            heuristics['both-pricereason'][app] = {}
            for threads in EXP[app]:
                for vm in EXP[app][threads]:
                    minvcpus = 2*EXP[app][threads][vm]['utilization']*INSTANCES[vm]['vcpu']
                    selected, found = heuristic_algorithm(vm, minvcpus, minvcpus, app, compare_type='pricereason')
                    if not found:
                        minvcpus = EXP[app][threads][vm]['utilization']*INSTANCES[vm]['vcpu']
                        selected, found = heuristic_algorithm(vm, minvcpus, minvcpus, app, compare_type='pricereason')
                    calculate_overheads('both-pricereason', threads, app, vm, selected)

            # top-down-pricereason-heuristic
            print("top-down-pricereason-heuristic")
            heuristics['topdown-pricereason'][app] = {}
            for threads in EXP[app]:
                for vm in EXP[app][threads]:
                    # Get min of vcpus is the two times the amount shown in utilization rate
                    minvcpus = EXP[app][threads][vm]['utilization']*INSTANCES[vm]['vcpu']
                    # Get max of vcpus is the two times the amount shown in utilization rate
                    maxvcpus = 2*EXP[app][threads][vm]['utilization']*INSTANCES[vm]['vcpu']
                    
                    selected, found = heuristic_algorithm(vm, minvcpus, maxvcpus, app, compare_type='pricereason')

                    calculate_overheads('topdown-pricereason', threads, app, vm, selected)


    (open(EXPERIMENTS_FILE, 'w+')).write(json.dumps(heuristics))