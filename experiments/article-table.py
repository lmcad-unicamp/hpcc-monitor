from experiments import scipy, json, os, re, heuristic_name, article_heuristics, sortedbyvcpu, INSTANCES 
from pprint import pprint

FILE = 'results/exp1.json'
with open(FILE, 'r') as fp:
    heuristics = json.load(fp)


print("==============================EXPERIMENT 1======================")
threads_column = False
utilization_column = True 
APPLICATION = 'LU'
VM = {}
for heuristic in article_heuristics:
    for t in heuristics[heuristic][APPLICATION]:
        for vm in heuristics[heuristic][APPLICATION][t]:
            if heuristics[heuristic][APPLICATION][t][vm]['current']['experiment']:
                if vm not in VM:
                    VM[vm] = {}
                VM[vm][heuristic] = heuristics[heuristic][APPLICATION][t][vm]

sortedbyvcpu_filtered = []
for vm in sortedbyvcpu:
    if vm in VM:
        sortedbyvcpu_filtered.append(vm)

data = {}
for heuristic in article_heuristics:
    data[heuristic] = {}
    data[heuristic]['perf'] = []
    data[heuristic]['cost'] = []
    for t in heuristics[heuristic][APPLICATION]:
        for vm in heuristics[heuristic][APPLICATION][t]:
            if vm != heuristics[heuristic][APPLICATION][t][vm]['selected']['instance']['name']:
                data[heuristic]['perf'].append(heuristics[heuristic][APPLICATION][t][vm]['ovperf'])
                data[heuristic]['cost'].append(heuristics[heuristic][APPLICATION][t][vm]['ovcost'])


# Table no1 - seletion in each execution
vcpus_border= min([t for t in heuristics['vcpu']])
print("\n\n")
for vm in sortedbyvcpu_filtered:
    border = VM[vm]['vcpu']['current']['instance']['vcpu']
    if vcpus_border != border:
        print('\\Xhline{5\\arrayrulewidth}')
    else:
        print('\\hline')
    vcpus_border = border
    st = ''
    st += '\\scriptsize{\\instance{'+ INSTANCES[vm]['subname'] +'}}' + ' & '
    #st += str(INSTANCES[vm]['vcpu']) + ' & '
    st += '\\scriptsize{' + str(INSTANCES[vm]['price']) +'}' + ' & '
    st += '\\scriptsize{' + str(round(INSTANCES[vm]['pricereason'],3)) +'}' + ' & '
    st += '\\scriptsize{' + str(int(VM[vm]['vcpu']['current']['threads'])) +'}' + ' & '
    #st += str(int(VM[vm]['vcpu']['current']['utilization']*100)) + '\% & '

    for h in article_heuristics:
        if VM[vm][h]['selected']['instance']['name'] == vm:
            st += '\\scriptsize{\\textcolor{gray}{\\instance{'+ VM[vm][h]['selected']['instance']['subname'] +'}}}'
        else:
            st += '\\scriptsize{\\instance{'+ VM[vm][h]['selected']['instance']['subname']+'}}'
        if h != 'cpu-pricereason':
            st+= '&'
    
    st += '\\\\'
    print(st)
print("\n\n")



print("==============================EXPERIMENT 2======================")

FILE = 'results/exp2.json'
with open(FILE, 'r') as fp:
    heuristics = json.load(fp)


threads_column = False
utilization_column = True 
APPLICATION = 'LU'
VM = {}
for heuristic in article_heuristics:
    for t in heuristics[heuristic][APPLICATION]:
        for vm in heuristics[heuristic][APPLICATION][t]:
            if heuristics[heuristic][APPLICATION][t][vm]['current']['experiment']:
                if vm not in VM:
                    VM[vm] = {}
                VM[vm][heuristic] = heuristics[heuristic][APPLICATION][t][vm]

sortedbyvcpu_filtered = []
for vm in sortedbyvcpu:
    if vm in VM:
        sortedbyvcpu_filtered.append(vm)

data = {}
for heuristic in article_heuristics:
    data[heuristic] = {}
    data[heuristic]['perf'] = []
    data[heuristic]['cost'] = []
    for t in heuristics[heuristic][APPLICATION]:
        for vm in heuristics[heuristic][APPLICATION][t]:
            if vm != heuristics[heuristic][APPLICATION][t][vm]['selected']['instance']['name']:
                data[heuristic]['perf'].append(heuristics[heuristic][APPLICATION][t][vm]['ovperf'])
                data[heuristic]['cost'].append(heuristics[heuristic][APPLICATION][t][vm]['ovcost'])


# Table no1 - seletion in each execution
vcpus_border= min([t for t in heuristics['vcpu']])
print("\n\n")
for vm in sortedbyvcpu_filtered:
    border = VM[vm]['vcpu']['current']['instance']['vcpu']
    if vcpus_border != border:
        print('\\Xhline{5\\arrayrulewidth}')
    else:
        print('\\hline')
    vcpus_border = border
    st = ''
    st += '\\scriptsize{\\instance{'+ INSTANCES[vm]['subname'] +'}}' + ' & '
    #st += str(INSTANCES[vm]['vcpu']) + ' & '
    st += '\\scriptsize{' + str(INSTANCES[vm]['price']) +'}' + ' & '
    st += '\\scriptsize{' + str(round(INSTANCES[vm]['pricereason'],3)) +'}' + ' & '
    st += '\\scriptsize{' + str(int(VM[vm]['vcpu']['current']['threads'])) +'}' + ' & '
    #st += str(int(VM[vm]['vcpu']['current']['utilization']*100)) + '\% & '

    for h in article_heuristics:
        if VM[vm][h]['selected']['instance']['name'] == vm:
            st += '\\scriptsize{\\textcolor{gray}{\\instance{'+ VM[vm][h]['selected']['instance']['subname'] +'}}}'
        else:
            st += '\\scriptsize{\\instance{'+ VM[vm][h]['selected']['instance']['subname']+'}}'
        if h != 'cpu-pricereason':
            st+= '&'
    
    st += '\\\\'
    print(st)
print("\n\n")
