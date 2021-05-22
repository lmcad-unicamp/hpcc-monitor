from experiments import scipy, json, os, re, heuristic_name, price_heuristics, pricereason_heuristics, sortedbyvcpu, INSTANCES 
from pprint import pprint

FILE = 'results/exp1.json'
with open(FILE, 'r') as fp:
    heuristics = json.load(fp)


print("==============================TABELAS PARA BT-1======================")
print("==============================PRICE-REASON======================")
print("==============================EXPERIMENT 1======================")
threads_column = False
utilization_column = True 
APPLICATION = 'BT'
THREAD = '4'
VM = {}
for heuristic in pricereason_heuristics:
    for vm in heuristics[heuristic][APPLICATION][THREAD]:
        if heuristics[heuristic][APPLICATION][THREAD][vm]['current']['experiment']:
            if vm not in VM:
                VM[vm] = {}
            VM[vm][heuristic] = heuristics[heuristic][APPLICATION][THREAD][vm]

sortedbyvcpu_filtered = []
for vm in sortedbyvcpu:
    if vm in VM:
        sortedbyvcpu_filtered.append(vm)

data = {}
for heuristic in pricereason_heuristics:
    data[heuristic] = {}
    data[heuristic]['perf'] = []
    data[heuristic]['cost'] = []
    for vm in heuristics[heuristic][APPLICATION][THREAD]:
        if vm != heuristics[heuristic][APPLICATION][THREAD][vm]['selected']['instance']['name']:
            data[heuristic]['perf'].append(heuristics[heuristic][APPLICATION][THREAD][vm]['ovperf'])
            data[heuristic]['cost'].append(heuristics[heuristic][APPLICATION][THREAD][vm]['ovcost'])


# Table no1 - seletion in each execution
vcpus_border= min([t for t in heuristics['vcpu-pricereason']])
print("\n\n")
for vm in sortedbyvcpu_filtered:
    border = VM[vm]['vcpu-pricereason']['current']['instance']['vcpu']
    if vcpus_border != border:
        print('\\Xhline{5\\arrayrulewidth}')
    else:
        print('\\hline')
    vcpus_border = border
    st = ''
    st += '\\instance{'+ INSTANCES[vm]['subname'] +'}' + ' & '
    st += str(INSTANCES[vm]['vcpu']) + ' & '
    st += str(INSTANCES[vm]['cpu']) + ' & '
    st += str(round(INSTANCES[vm]['pricereason'],2)) + ' & '
    st += str(int(VM[vm]['vcpu-pricereason']['current']['utilization']*100)) + '\% & '

    for h in pricereason_heuristics:
        if VM[vm][h]['selected']['instance']['name'] == vm:
            st += '\\textcolor{gray}{\\instance{'+ VM[vm][h]['selected']['instance']['subname'] +'}}'
        else:
            st += '\\instance{'+ VM[vm][h]['selected']['instance']['subname']+'}'
        if h != 'topdown-pricereason':
            st+= '&'
    
    st += '\\\\'
    print(st)
print("\n\n")

# Table no2 - overheads in each execution
vcpus_border= min([t for t in heuristics['vcpu']])
maxvalue=11
for vm in sortedbyvcpu_filtered:
    border = VM[vm]['vcpu-pricereason']['current']['instance']['vcpu']
    if vcpus_border != border:
        print('\\Xhline{5\\arrayrulewidth}')
    else:
        print('\\hline')
    vcpus_border = border
    st = ''
    st += '\\instance{'+ INSTANCES[vm]['subname'] +'}' + ' & '   
    for h in pricereason_heuristics:
        if VM[vm][h]['selected']['instance']['name'] == vm:
            st += ' & ' 
        else:
            perf = round(VM[vm][h]['ovperf'],2)
            if perf > 1.00:
                st += '\\cellcolor{greengradient!'+ str(int((perf-1.00)*100/(maxvalue-1.00))) +'}' 
            elif perf < 1.00:
                st += '\\cellcolor{redgradient!'+ str(int((1.00-perf)*100)) +'}' 
            st += str(perf) + ' & '

            cost = round(VM[vm][h]['ovcost'],2)
            if cost > 1.00:
                st += '\\cellcolor{greengradient!'+ str(int((cost-1.00)*100/(maxvalue-1.00))) +'}' 
            elif cost < 1.00:
                st += '\\cellcolor{redgradient!'+ str(int((1.00-cost)*100)) +'}' 
            st += str(cost)
        if h != 'topdown-pricereason':
            st+= '&'
    st += '\\\\'
    print(st)

print('\\Xhline{5\\arrayrulewidth}')
st = '\\shortstack{\\footnotesize{geometric}\\\\ \\footnotesize{mean}} &'
for h in pricereason_heuristics:
    perf = round(scipy.stats.mstats.gmean(data[h]['perf']),2)
    if perf > 1.00:
        st += '\\cellcolor{greengradient!'+ str(int((perf-1.00)*100/(maxvalue-1.00))) +'}' 
    elif perf < 1.00:
        st += '\\cellcolor{redgradient!'+ str(int((1.00-perf)*100)) +'}' 
    st += str(perf) + ' & '

    cost = round(scipy.stats.mstats.gmean(data[h]['cost']),2)
    if cost > 1.00:
        st += '\\cellcolor{greengradient!'+ str(int((cost-1.00)*100/(maxvalue-1.00))) +'}' 
    elif cost < 1.00:
        st += '\\cellcolor{redgradient!'+ str(int((1.00-cost)*100)) +'}' 
    st += str(cost)
    if pricereason_heuristics and h != 'topdown-pricereason':
        st+= '&'
st += '\\\\'
print(st)
print("\n\n")

print("==============================TABELAS PARA FT-1======================")
print("==============================PRICE-REASON======================")
print("==============================EXPERIMENT 1======================")
APPLICATION = 'FT'
THREADS = '4'
VM = {}
for heuristic in pricereason_heuristics:
    for vm in heuristics[heuristic][APPLICATION][THREADS]:
        if heuristics[heuristic][APPLICATION][THREADS][vm]['current']['experiment']:
            if vm not in VM:
                VM[vm] = {}
            VM[vm][heuristic] = heuristics[heuristic][APPLICATION][THREADS][vm]


sortedbyvcpu_filtered = []
for vm in sortedbyvcpu:
    if vm in VM:
        sortedbyvcpu_filtered.append(vm)

# Table no1 - seletion in each execution
vcpus_border= min([t for t in heuristics['vcpu-pricereason']])
print("\n\n")
for vm in sortedbyvcpu_filtered:
    border = VM[vm]['vcpu-pricereason']['current']['instance']['vcpu']
    if vcpus_border != border:
        print('\\Xhline{4\\arrayrulewidth}')
    else:
        print('\\hline')
    vcpus_border = border
    st = ''
    st += '\\instance{'+ INSTANCES[vm]['subname'] +'}' + ' & '
    st += str(INSTANCES[vm]['vcpu']) + ' & '
    st += str(INSTANCES[vm]['cpu']) + ' & '
    st += str(round(INSTANCES[vm]['pricereason'],3)) + ' & '
    st += str(int(VM[vm]['vcpu-pricereason']['current']['utilization']*100)) + '\% & '

    for h in pricereason_heuristics:
        if VM[vm][h]['selected']['instance']['name'] == vm:
            st += '\\textcolor{gray}{\\instance{'+ VM[vm][h]['selected']['instance']['subname'] +'}}'
        else:
            st += '\\instance{'+ VM[vm][h]['selected']['instance']['subname']+'}'
        if h != 'topdown-pricereason':
            st+= '&'
    
    st += '\\\\'
    print(st)
print("\n\n")

THREADS = '16'
VM = {}
for heuristic in pricereason_heuristics:
    for vm in heuristics[heuristic][APPLICATION][THREADS]:
        if heuristics[heuristic][APPLICATION][THREADS][vm]['current']['experiment']:
            if vm not in VM:
                VM[vm] = {}
            VM[vm][heuristic] = heuristics[heuristic][APPLICATION][THREADS][vm]

sortedbyvcpu_filtered = []
for vm in sortedbyvcpu:
    if vm in VM:
        sortedbyvcpu_filtered.append(vm)

# Table no1 - seletion in each execution
vcpus_border= min([t for t in heuristics['vcpu-pricereason']])
print("\n\n")
for vm in sortedbyvcpu_filtered:
    border = VM[vm]['vcpu-pricereason']['current']['instance']['vcpu']
    if vcpus_border != border:
        print('\\Xhline{4\\arrayrulewidth}')
    else:
        print('\\hline')
    vcpus_border = border
    st = ''
    st += '\\instance{'+ INSTANCES[vm]['subname'] +'}' + ' & '
    st += str(INSTANCES[vm]['vcpu']) + ' & '
    st += str(INSTANCES[vm]['cpu']) + ' & '
    st += str(round(INSTANCES[vm]['pricereason'],3)) + ' & '
    st += str(int(VM[vm]['vcpu-pricereason']['current']['utilization']*100)) + '\% & '

    for h in pricereason_heuristics:
        if VM[vm][h]['selected']['instance']['name'] == vm:
            st += '\\textcolor{gray}{\\instance{'+ VM[vm][h]['selected']['instance']['subname'] +'}}'
        else:
            st += '\\instance{'+ VM[vm][h]['selected']['instance']['subname']+'}'
        if h != 'topdown-pricereason':
            st+= '&'    
    st += '\\\\'
    print(st)
print("\n\n")





FILE = 'results/exp2.json'
with open(FILE, 'r') as fp:
    heuristics = json.load(fp)

print("==============================TABELAS PARA BT-1======================")
print("==============================PRICE-REASON======================")
print("==============================EXPERIMENT 2======================")
threads_column = False
utilization_column = True 
APPLICATION = 'BT'
VM = {}
for heuristic in pricereason_heuristics:
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
for heuristic in pricereason_heuristics:
    data[heuristic] = {}
    data[heuristic]['perf'] = []
    data[heuristic]['cost'] = []
    for t in heuristics[heuristic][APPLICATION]:
        for vm in heuristics[heuristic][APPLICATION][t]:
            if vm != heuristics[heuristic][APPLICATION][t][vm]['selected']['instance']['name']:
                data[heuristic]['perf'].append(heuristics[heuristic][APPLICATION][t][vm]['ovperf'])
                data[heuristic]['cost'].append(heuristics[heuristic][APPLICATION][t][vm]['ovcost'])


# Table no1 - seletion in each execution
vcpus_border= min([t for t in heuristics['vcpu-pricereason']])
print("\n\n")
for vm in sortedbyvcpu_filtered:
    border = VM[vm]['vcpu-pricereason']['current']['instance']['vcpu']
    if vcpus_border != border:
        print('\\Xhline{5\\arrayrulewidth}')
    else:
        print('\\hline')
    vcpus_border = border
    st = ''
    st += '\\instance{'+ INSTANCES[vm]['subname'] +'}' + ' & '
    st += str(INSTANCES[vm]['vcpu']) + ' & '
    st += str(INSTANCES[vm]['cpu']) + ' & '
    st += str(round(INSTANCES[vm]['pricereason'],3)) + ' & '
    st += str(int(VM[vm]['vcpu-pricereason']['current']['threads'])) + ' & '

    for h in pricereason_heuristics:
        if VM[vm][h]['selected']['instance']['name'] == vm:
            st += '\\textcolor{gray}{\\instance{'+ VM[vm][h]['selected']['instance']['subname'] +'}}'
        else:
            st += '\\instance{'+ VM[vm][h]['selected']['instance']['subname']+'}'
        if h != 'topdown-pricereason':
            st+= '&'
    
    st += '\\\\'
    print(st)
print("\n\n")

# Table no2 - overheads in each execution
vcpus_border= min([t for t in heuristics['vcpu']])
maxvalue=11
for vm in sortedbyvcpu_filtered:
    border = VM[vm]['vcpu-pricereason']['current']['instance']['vcpu']
    if vcpus_border != border:
        print('\\Xhline{5\\arrayrulewidth}')
    else:
        print('\\hline')
    vcpus_border = border
    st = ''
    st += '\\instance{'+ INSTANCES[vm]['subname'] +'}' + ' & '   
    for h in pricereason_heuristics:
        if VM[vm][h]['selected']['instance']['name'] == vm:
            st += ' & ' 
        else:
            perf = round(VM[vm][h]['ovperf'],2)
            if perf > 1.00:
                st += '\\cellcolor{greengradient!'+ str(int((perf-1.00)*100/(maxvalue-1.00))) +'}' 
            elif perf < 1.00:
                st += '\\cellcolor{redgradient!'+ str(int((1.00-perf)*100)) +'}' 
            st += str(perf) + ' & '

            cost = round(VM[vm][h]['ovcost'],2)
            if cost > 1.00:
                st += '\\cellcolor{greengradient!'+ str(int((cost-1.00)*100/(maxvalue-1.00))) +'}' 
            elif cost < 1.00:
                st += '\\cellcolor{redgradient!'+ str(int((1.00-cost)*100)) +'}' 
            st += str(cost)
        if h != 'topdown-pricereason':
            st+= '&'
    st += '\\\\'
    print(st)

print('\\Xhline{5\\arrayrulewidth}')
st = '\\shortstack{\\footnotesize{geometric}\\\\ \\footnotesize{mean}} &'
for h in pricereason_heuristics:
    perf = round(scipy.stats.mstats.gmean(data[h]['perf']),2)
    if perf > 1.00:
        st += '\\cellcolor{greengradient!'+ str(int((perf-1.00)*100/(maxvalue-1.00))) +'}' 
    elif perf < 1.00:
        st += '\\cellcolor{redgradient!'+ str(int((1.00-perf)*100)) +'}' 
    st += str(perf) + ' & '

    cost = round(scipy.stats.mstats.gmean(data[h]['cost']),2)
    if cost > 1.00:
        st += '\\cellcolor{greengradient!'+ str(int((cost-1.00)*100/(maxvalue-1.00))) +'}' 
    elif cost < 1.00:
        st += '\\cellcolor{redgradient!'+ str(int((1.00-cost)*100)) +'}' 
    st += str(cost)
    if pricereason_heuristics and h != 'topdown-pricereason':
        st+= '&'
st += '\\\\'
print(st)
print("\n\n")

print("==============================TABELAS PARA LU-1======================")
print("==============================PRICE-REASON======================")
print("==============================EXPERIMENT 2======================")
threads_column = False
utilization_column = True 
APPLICATION = 'LU'
VM = {}
for heuristic in pricereason_heuristics:
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
for heuristic in pricereason_heuristics:
    data[heuristic] = {}
    data[heuristic]['perf'] = []
    data[heuristic]['cost'] = []
    for t in heuristics[heuristic][APPLICATION]:
        for vm in heuristics[heuristic][APPLICATION][t]:
            data[heuristic]['perf'].append(heuristics[heuristic][APPLICATION][t][vm]['ovperf'])
            data[heuristic]['cost'].append(heuristics[heuristic][APPLICATION][t][vm]['ovcost'])


# Table no1 - seletion in each execution
vcpus_border= min([t for t in heuristics['vcpu-pricereason']])
print("\n\n")
for vm in sortedbyvcpu_filtered:
    border = VM[vm]['vcpu-pricereason']['current']['instance']['vcpu']
    if vcpus_border != border:
        print('\\Xhline{5\\arrayrulewidth}')
    else:
        print('\\hline')
    vcpus_border = border
    st = ''
    st += '\\instance{'+ INSTANCES[vm]['subname'] +'}' + ' & '
    st += str(INSTANCES[vm]['vcpu']) + ' & '
    st += str(INSTANCES[vm]['cpu']) + ' & '
    st += str(round(INSTANCES[vm]['pricereason'],3)) + ' & '
    st += str(int(VM[vm]['vcpu-pricereason']['current']['threads'])) + ' & '

    for h in pricereason_heuristics:
        if VM[vm][h]['selected']['instance']['name'] == vm:
            st += '\\textcolor{gray}{\\instance{'+ VM[vm][h]['selected']['instance']['subname'] +'}}'
        else:
            st += '\\instance{'+ VM[vm][h]['selected']['instance']['subname']+'}'
        if h != 'topdown-pricereason':
            st+= '&'
    
    st += '\\\\'
    print(st)
print("\n\n")

# Table no2 - overheads in each execution
vcpus_border= min([t for t in heuristics['vcpu']])
maxvalue=11
for vm in sortedbyvcpu_filtered:
    border = VM[vm]['vcpu-pricereason']['current']['instance']['vcpu']
    if vcpus_border != border:
        print('\\Xhline{5\\arrayrulewidth}')
    else:
        print('\\hline')
    vcpus_border = border
    st = ''
    st += '\\instance{'+ INSTANCES[vm]['subname'] +'}' + ' & '   
    for h in pricereason_heuristics:
        if VM[vm][h]['selected']['instance']['name'] == vm:
            st += ' & ' 
        else:
            perf = round(VM[vm][h]['ovperf'],2)
            if perf > 1.00:
                st += '\\cellcolor{greengradient!'+ str(int((perf-1.00)*100/(maxvalue-1.00))) +'}' 
            elif perf < 1.00:
                st += '\\cellcolor{redgradient!'+ str(int((1.00-perf)*100)) +'}' 
            st += str(perf) + ' & '

            cost = round(VM[vm][h]['ovcost'],2)
            if cost > 1.00:
                st += '\\cellcolor{greengradient!'+ str(int((cost-1.00)*100/(maxvalue-1.00))) +'}' 
            elif cost < 1.00:
                st += '\\cellcolor{redgradient!'+ str(int((1.00-cost)*100)) +'}' 
            st += str(cost)
        if h != 'topdown-pricereason':
            st+= '&'
    st += '\\\\'
    print(st)

print('\\Xhline{5\\arrayrulewidth}')
st = '\\shortstack{\\footnotesize{geometric}\\\\ \\footnotesize{mean}} &'
for h in pricereason_heuristics:
    perf = round(scipy.stats.mstats.gmean(data[h]['perf']),2)
    if perf > 1.00:
        st += '\\cellcolor{greengradient!'+ str(int((perf-1.00)*100/(maxvalue-1.00))) +'}' 
    elif perf < 1.00:
        st += '\\cellcolor{redgradient!'+ str(int((1.00-perf)*100)) +'}' 
    st += str(perf) + ' & '

    cost = round(scipy.stats.mstats.gmean(data[h]['cost']),2)
    if cost > 1.00:
        st += '\\cellcolor{greengradient!'+ str(int((cost-1.00)*100/(maxvalue-1.00))) +'}' 
    elif cost < 1.00:
        st += '\\cellcolor{redgradient!'+ str(int((1.00-cost)*100)) +'}' 
    st += str(cost)
    if pricereason_heuristics and h != 'topdown-pricereason':
        st+= '&'
st += '\\\\'
print(st)
print("\n\n")


print("==============================TABELAS PARA FT-1======================")
print("==============================PRICE-REASON======================")
print("==============================EXPERIMENT 2======================")
threads_column = False
utilization_column = True 
APPLICATION = 'FT'
VM = {}
for heuristic in pricereason_heuristics:
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
for heuristic in pricereason_heuristics:
    data[heuristic] = {}
    data[heuristic]['perf'] = []
    data[heuristic]['cost'] = []
    for t in heuristics[heuristic][APPLICATION]:
        for vm in heuristics[heuristic][APPLICATION][t]:
            data[heuristic]['perf'].append(heuristics[heuristic][APPLICATION][t][vm]['ovperf'])
            data[heuristic]['cost'].append(heuristics[heuristic][APPLICATION][t][vm]['ovcost'])


# Table no1 - seletion in each execution
vcpus_border= min([t for t in heuristics['vcpu-pricereason']])
print("\n\n")
for vm in sortedbyvcpu_filtered:
    border = VM[vm]['vcpu-pricereason']['current']['instance']['vcpu']
    if vcpus_border != border:
        print('\\Xhline{5\\arrayrulewidth}')
    else:
        print('\\hline')
    vcpus_border = border
    st = ''
    st += '\\instance{'+ INSTANCES[vm]['subname'] +'}' + ' & '
    st += str(INSTANCES[vm]['vcpu']) + ' & '
    st += str(INSTANCES[vm]['cpu']) + ' & '
    st += str(round(INSTANCES[vm]['pricereason'],3)) + ' & '
    st += str(int(VM[vm]['vcpu-pricereason']['current']['threads'])) + ' & '

    for h in pricereason_heuristics:
        if VM[vm][h]['selected']['instance']['name'] == vm:
            st += '\\textcolor{gray}{\\instance{'+ VM[vm][h]['selected']['instance']['subname'] +'}}'
        else:
            st += '\\instance{'+ VM[vm][h]['selected']['instance']['subname']+'}'
        if h != 'topdown-pricereason':
            st+= '&'
    
    st += '\\\\'
    print(st)
print("\n\n")

# Table no2 - overheads in each execution
vcpus_border= min([t for t in heuristics['vcpu']])
maxvalue=11
for vm in sortedbyvcpu_filtered:
    border = VM[vm]['vcpu-pricereason']['current']['instance']['vcpu']
    if vcpus_border != border:
        print('\\Xhline{5\\arrayrulewidth}')
    else:
        print('\\hline')
    vcpus_border = border
    st = ''
    st += '\\instance{'+ INSTANCES[vm]['subname'] +'}' + ' & '   
    for h in pricereason_heuristics:
        if VM[vm][h]['selected']['instance']['name'] == vm:
            st += ' & ' 
        else:
            perf = round(VM[vm][h]['ovperf'],2)
            if perf > 1.00:
                st += '\\cellcolor{greengradient!'+ str(int((perf-1.00)*100/(maxvalue-1.00))) +'}' 
            elif perf < 1.00:
                st += '\\cellcolor{redgradient!'+ str(int((1.00-perf)*100)) +'}' 
            st += str(perf) + ' & '

            cost = round(VM[vm][h]['ovcost'],2)
            if cost > 1.00:
                st += '\\cellcolor{greengradient!'+ str(int((cost-1.00)*100/(maxvalue-1.00))) +'}' 
            elif cost < 1.00:
                st += '\\cellcolor{redgradient!'+ str(int((1.00-cost)*100)) +'}' 
            st += str(cost)
        if h != 'topdown-pricereason':
            st+= '&'
    st += '\\\\'
    print(st)

print('\\Xhline{5\\arrayrulewidth}')
st = '\\shortstack{\\footnotesize{geometric}\\\\ \\footnotesize{mean}} &'
for h in pricereason_heuristics:
    perf = round(scipy.stats.mstats.gmean(data[h]['perf']),2)
    if perf > 1.00:
        st += '\\cellcolor{greengradient!'+ str(int((perf-1.00)*100/(maxvalue-1.00))) +'}' 
    elif perf < 1.00:
        st += '\\cellcolor{redgradient!'+ str(int((1.00-perf)*100)) +'}' 
    st += str(perf) + ' & '

    cost = round(scipy.stats.mstats.gmean(data[h]['cost']),2)
    if cost > 1.00:
        st += '\\cellcolor{greengradient!'+ str(int((cost-1.00)*100/(maxvalue-1.00))) +'}' 
    elif cost < 1.00:
        st += '\\cellcolor{redgradient!'+ str(int((1.00-cost)*100)) +'}' 
    st += str(cost)
    if pricereason_heuristics and h != 'topdown-pricereason':
        st+= '&'
st += '\\\\'
print(st)
print("\n\n")
exit()
