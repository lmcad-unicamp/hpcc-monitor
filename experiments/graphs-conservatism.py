from experiments import scipy, json, np, os, re, heuristic_name, price_heuristics, pricereason_heuristics, sortedbyvcpu, INSTANCES 
from pprint import pprint
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import matplotlib.cm as cm

# Graphs
plt.style.use('seaborn')
markers = ['1', '2', '3', '4', '+', 'x', '|', '_']
colors = ['#FF0000', '#0000FF', '#FF6600', '#0cc202', '#c4a400',  '#e30079', '#7704c9', '#000000']
def mean_confidence_interval(data, confidence=0.95):
    a = 1.0 * np.array(data)
    n = len(a)
    m, se = np.mean(a), scipy.stats.sem(a)
    h = se * scipy.stats.t.ppf((1 + confidence) / 2., n-1)
    return h

f = lambda m,c: plt.plot([],[],marker=m, color=c, ls="none")[0]

#----------------------------------------------- price
FILE = 'results/exp2.40.json'
with open(FILE, 'r') as fp:
    heuristics = json.load(fp)
GRAPHS_DIR = 'graphs'
if not os.path.exists(GRAPHS_DIR):
    os.makedirs(GRAPHS_DIR)

data = {}
for heuristic in price_heuristics:
    data[heuristic] = {'change': 0, 'nochange': 0}
    for app in heuristics[heuristic]:
        for threads in heuristics[heuristic][app]:
            for vm in heuristics[heuristic][app][threads]:
                if vm != heuristics[heuristic][app][threads][vm]['selected']['instance']['name']:
                    data[heuristic]['change'] += 1
                else:
                    data[heuristic]['nochange'] += 1

fig, ax = plt.subplots()

temp = np.array([])
gainloss = np.array([data[h]['change'] for h in price_heuristics])
ax.bar([heuristic_name[h] for h in price_heuristics], gainloss, 0.35, 
            label='Different as the current', color='#525150')
nochange = np.array([data[h]['nochange'] for h in price_heuristics])
ax.bar([heuristic_name[h] for h in price_heuristics], nochange, 0.35, 
            label='Same as the current', color='#b8b7b4', bottom=gainloss)
lgnd = plt.legend(bbox_to_anchor=(0.5, 1.3), loc='upper center', ncol=1, fontsize=20, 
                    facecolor='white', frameon=True)
for i in lgnd.legendHandles:
    i._sizes = [50]
#lgnd.get_frame().set_linewidth(100)
plt.ylabel('Amount of experiments', fontsize=20)
plt.yticks(fontsize=20)
plt.ylim(0, 600)
plt.xticks(fontsize=20)
plt.savefig(GRAPHS_DIR+'/'+'bar-nochange.svg', dpi=100, 
            bbox_inches='tight', format='svg', pad_inches = 0)
plt.show()
plt.clf()



data = {}
for heuristic in price_heuristics:
    data[heuristic] = {'perf': 0, 'both': 0, 'nochange': 0, 'gain/loss': 0, 'cost': 0}
    for app in heuristics[heuristic]:
        for threads in heuristics[heuristic][app]:
            for vm in heuristics[heuristic][app][threads]:
                if vm != heuristics[heuristic][app][threads][vm]['selected']['instance']['name']:
                    print(round(heuristics[heuristic][app][threads][vm]['ovcost'], 1))
                    if round(heuristics[heuristic][app][threads][vm]['ovcost'], 1) == 1.00 and round(heuristics[heuristic][app][threads][vm]['ovperf'], 1) == 1.00:
                        data[heuristic]['both'] += 1
                    elif round(heuristics[heuristic][app][threads][vm]['ovcost'], 1) == 1.00:
                        data[heuristic]['cost'] += 1
                    elif round(heuristics[heuristic][app][threads][vm]['ovperf'], 1) == 1.00:
                        data[heuristic]['perf'] += 1
                    else:
                        data[heuristic]['gain/loss'] += 1
                else:
                    data[heuristic]['nochange'] += 1

fig, ax = plt.subplots()
temp = np.array([])
cost = np.array([data[h]['cost'] for h in price_heuristics])
ax.bar([heuristic_name[h] for h in price_heuristics], cost, 0.35, label='Same cost', color=colors[1])
both = np.array([data[h]['both'] for h in price_heuristics])
ax.bar([heuristic_name[h] for h in price_heuristics], both, 0.35, label='Same cost and performance', color=colors[3], bottom=cost)
perf = np.array([data[h]['perf'] for h in price_heuristics])
ax.bar([heuristic_name[h] for h in price_heuristics], perf, 0.35, label='Same performance', color=colors[4], bottom=cost+both)
gainloss = np.array([data[h]['gain/loss'] for h in price_heuristics])
ax.bar([heuristic_name[h] for h in price_heuristics], gainloss, 0.35, label='Different cost and performance', color=colors[2], bottom=perf+cost+both)
print(cost)
print(both)
print(perf)
print(gainloss)
lgnd = plt.legend(bbox_to_anchor=(0.5, 1.3), loc='upper center', ncol=1, fontsize=20, 
                    facecolor='white', frameon=True)
for i in lgnd.legendHandles:
    i._sizes = [50]
#lgnd.get_frame().set_linewidth(100)
plt.ylabel('Amount of experiments', fontsize=20)
plt.yticks(fontsize=20)
plt.ylim(0, 600)
plt.xticks(fontsize=20)
plt.savefig(GRAPHS_DIR+'/'+'bar-change.svg', dpi=100, 
            bbox_inches='tight', format='svg', pad_inches = 0)
plt.show()
plt.clf()


data = {}
for heuristic in price_heuristics:
    data[heuristic] = {}
    data[heuristic]['perf'] = []
    data[heuristic]['cost'] = []
    for app in heuristics[heuristic]:
        for threads in heuristics[heuristic][app]:
            for vm in heuristics[heuristic][app][threads]:
                if vm != heuristics[heuristic][app][threads][vm]['selected']['instance']['name']:
                    data[heuristic]['perf'].append(heuristics[heuristic][app][threads][vm]['ovperf'])
                    data[heuristic]['cost'].append(heuristics[heuristic][app][threads][vm]['ovcost'])

for h,c in zip(data, colors):
        plt.errorbar(scipy.stats.mstats.gmean(data[h]['cost']), 
                scipy.stats.mstats.gmean(data[h]['perf']),
                yerr=mean_confidence_interval(data[h]['perf']),
                xerr=mean_confidence_interval(data[h]['cost']), 
                c=c, alpha=0.5, label=heuristic_name[h], fmt='o')

lgnd = plt.legend(loc='lower left', ncol=1)
for i in lgnd.legendHandles:
    i._sizes = [10]
plt.ylabel("Performance Speedup")
plt.xlabel("Cost Reduction")
plt.hlines(1, 0.99, 1.6, color='#000')
plt.vlines(1, 0.65, 1.15, color='#000')
plt.xlim(0.99, 1.6)
plt.ylim(0.65, 1.01)
plt.savefig(GRAPHS_DIR+'/'+'heuristics-mean-onlychanges.svg', dpi=100,
            bbox_inches='tight', format='svg', pad_inches = 0)
plt.show()
plt.clf()


data = {'cpu': {'perf': [], 'cost': []},
        'both': {'perf': [], 'cost': []},
        'topdown': {'perf': [], 'cost': []}}
fig = plt.figure(figsize=(6.4, 3.5))
for app in heuristics['cpu']:
    for threads in heuristics['cpu'][app]:
        for vm in heuristics['cpu'][app][threads]:
            if (heuristics['cpu'][app][threads][vm]['selected']['instance']['name'] == vm):
                data['cpu']['perf'].append(heuristics['cpu'][app][threads][vm]['ovperf'])
                data['cpu']['cost'].append(heuristics['cpu'][app][threads][vm]['ovcost'])
                data['both']['perf'].append(heuristics['both'][app][threads][vm]['ovperf'])
                data['both']['cost'].append(heuristics['both'][app][threads][vm]['ovcost'])
                data['topdown']['perf'].append(heuristics['topdown'][app][threads][vm]['ovperf'])
                data['topdown']['cost'].append(heuristics['topdown'][app][threads][vm]['ovcost'])

plt.errorbar(scipy.stats.mstats.gmean(data['cpu']['cost']), 
        scipy.stats.mstats.gmean(data['cpu']['perf']),
        yerr=mean_confidence_interval(data['cpu']['perf']),
        xerr=mean_confidence_interval(data['cpu']['cost']), 
        c=colors[1], alpha=0.5, label=heuristic_name['cpu'], fmt='o')
plt.errorbar(scipy.stats.mstats.gmean(data['both']['cost']), 
        scipy.stats.mstats.gmean(data['both']['perf']),
        yerr=mean_confidence_interval(data['both']['perf']),
        xerr=mean_confidence_interval(data['both']['cost']), 
        c=colors[2], alpha=0.5, label=heuristic_name['both'], fmt='o')
plt.errorbar(scipy.stats.mstats.gmean(data['topdown']['cost']), 
        scipy.stats.mstats.gmean(data['topdown']['perf']),
        yerr=mean_confidence_interval(data['topdown']['perf']),
        xerr=mean_confidence_interval(data['topdown']['cost']), 
        c=colors[3], alpha=0.5, label=heuristic_name['topdown'], fmt='o')

lgnd = plt.legend(loc='lower right')
for i in lgnd.legendHandles:
    i._sizes = [10]
plt.ylabel("Performance Speedup")
plt.xlabel("Cost Reduction")
plt.hlines(1, 0.90, 1.2, color='#000')
plt.vlines(1, 0.8, 1.01, color='#000')
plt.xlim(0.99, 1.2)
plt.ylim(0.85, 1.01)
plt.xticks([1.00, 1.1, 1.2])
plt.yticks([0.85, 0.9, 0.95, 1.00])
plt.savefig(GRAPHS_DIR+'/'+'heuristics-mean-cpu-notchanges.svg', dpi=100,
            bbox_inches='tight', format='svg', pad_inches = 0)
plt.show()
plt.clf()


#----------------------------------------------- price-reason

data = {}
for heuristic in pricereason_heuristics:
    data[heuristic] = {'change': 0, 'nochange': 0}
    for app in heuristics[heuristic]:
        for threads in heuristics[heuristic][app]:
            for vm in heuristics[heuristic][app][threads]:
                if vm != heuristics[heuristic][app][threads][vm]['selected']['instance']['name']:
                    data[heuristic]['change'] += 1
                else:
                    data[heuristic]['nochange'] += 1

fig, ax = plt.subplots()

temp = np.array([])
gainloss = np.array([data[h]['change'] for h in pricereason_heuristics])
ax.bar([heuristic_name[h] for h in pricereason_heuristics], gainloss, 0.35, 
            label='Different as the current', color='#525150')
nochange = np.array([data[h]['nochange'] for h in pricereason_heuristics])
ax.bar([heuristic_name[h] for h in pricereason_heuristics], nochange, 0.35, 
            label='Same as the current', color='#b8b7b4', bottom=gainloss)
lgnd = plt.legend(bbox_to_anchor=(0.5, 1.3), loc='upper center', ncol=1, fontsize=20, 
                    facecolor='white', frameon=True)
for i in lgnd.legendHandles:
    i._sizes = [50]
#lgnd.get_frame().set_linewidth(100)
plt.ylabel('Amount of experiments', fontsize=20)
plt.yticks(fontsize=20)
plt.xticks(fontsize=20)
plt.ylim(0, 600)
plt.savefig(GRAPHS_DIR+'/'+'bar-pr-nochange.svg', dpi=100, 
            bbox_inches='tight', format='svg', pad_inches = 0)
plt.show()
plt.clf()



data = {}
for heuristic in pricereason_heuristics:
    data[heuristic] = {'perf': 0, 'both': 0, 'nochange': 0, 'gain/loss': 0, 'cost': 0}
    for app in heuristics[heuristic]:
        for threads in heuristics[heuristic][app]:
            for vm in heuristics[heuristic][app][threads]:
                if vm != heuristics[heuristic][app][threads][vm]['selected']['instance']['name']:
                    if round(heuristics[heuristic][app][threads][vm]['ovcost'], 1) == 1.00 and round(heuristics[heuristic][app][threads][vm]['ovperf'], 1) == 1.00:
                        data[heuristic]['both'] += 1
                    elif round(heuristics[heuristic][app][threads][vm]['ovcost'], 1) == 1.00:
                        data[heuristic]['cost'] += 1
                    elif round(heuristics[heuristic][app][threads][vm]['ovperf'], 1) == 1.00:
                        data[heuristic]['perf'] += 1
                    else:
                        data[heuristic]['gain/loss'] += 1
                else:
                    data[heuristic]['nochange'] += 1

fig, ax = plt.subplots()
temp = np.array([])
cost = np.array([data[h]['cost'] for h in pricereason_heuristics])
ax.bar([heuristic_name[h] for h in pricereason_heuristics], cost, 0.35, label='Same cost', color=colors[1])
both = np.array([data[h]['both'] for h in pricereason_heuristics])
ax.bar([heuristic_name[h] for h in pricereason_heuristics], both, 0.35, label='Same cost and performance', color=colors[3], bottom=cost)
perf = np.array([data[h]['perf'] for h in pricereason_heuristics])
ax.bar([heuristic_name[h] for h in pricereason_heuristics], perf, 0.35, label='Same performance', color=colors[4], bottom=cost+both)
gainloss = np.array([data[h]['gain/loss'] for h in pricereason_heuristics])
ax.bar([heuristic_name[h] for h in pricereason_heuristics], gainloss, 0.35, label='Different cost and performance', color=colors[2], bottom=perf+cost+both)
print(cost)
print(both)
print(perf)
print(gainloss)
lgnd = plt.legend(bbox_to_anchor=(0.5, 1.3), loc='upper center', ncol=1, fontsize=20, 
                    facecolor='white', frameon=True)
for i in lgnd.legendHandles:
    i._sizes = [50]
#lgnd.get_frame().set_linewidth(100)
plt.ylabel('Amount of experiments', fontsize=20)
plt.yticks(fontsize=20)
plt.ylim(0, 600)
plt.xticks(fontsize=20)
plt.savefig(GRAPHS_DIR+'/'+'bar-pr-change.svg', dpi=100, 
            bbox_inches='tight', format='svg', pad_inches = 0)
plt.show()
plt.clf()


data = {}
for heuristic in pricereason_heuristics:
    data[heuristic] = {}
    data[heuristic]['perf'] = []
    data[heuristic]['cost'] = []
    for app in heuristics[heuristic]:
        for threads in heuristics[heuristic][app]:
            for vm in heuristics[heuristic][app][threads]:
                if vm != heuristics[heuristic][app][threads][vm]['selected']['instance']['name']:
                    data[heuristic]['perf'].append(heuristics[heuristic][app][threads][vm]['ovperf'])
                    data[heuristic]['cost'].append(heuristics[heuristic][app][threads][vm]['ovcost'])

for h,c in zip(data, colors[4:]):
        plt.errorbar(scipy.stats.mstats.gmean(data[h]['cost']), 
                scipy.stats.mstats.gmean(data[h]['perf']),
                yerr=mean_confidence_interval(data[h]['perf']),
                xerr=mean_confidence_interval(data[h]['cost']), 
                c=c, alpha=0.5, label=heuristic_name[h], fmt='o')

lgnd = plt.legend(loc='lower left', ncol=1)
for i in lgnd.legendHandles:
    i._sizes = [10]
plt.ylabel("Performance Speedup")
plt.xlabel("Cost Reduction")
plt.hlines(1, 0.99, 1.6, color='#000')
plt.vlines(1, 0.65, 1.15, color='#000')
plt.xlim(0.99, 1.52)
plt.ylim(0.65, 1.15)
plt.savefig(GRAPHS_DIR+'/'+'heuristics-mean-pr-onlychanges.svg', dpi=100,
            bbox_inches='tight', format='svg', pad_inches = 0)
plt.show()
plt.clf()



data = {'cpu-pricereason': {'perf': [], 'cost': []},
        'both-pricereason': {'perf': [], 'cost': []},
        'topdown-pricereason': {'perf': [], 'cost': []}}
fig = plt.figure(figsize=(6.4, 3.5))
for app in heuristics['cpu-pricereason']:
    for threads in heuristics['cpu-pricereason'][app]:
        for vm in heuristics['cpu-pricereason'][app][threads]:
            if (heuristics['cpu-pricereason'][app][threads][vm]['selected']['instance']['name'] == vm):
                data['cpu-pricereason']['perf'].append(heuristics['cpu-pricereason'][app][threads][vm]['ovperf'])
                data['cpu-pricereason']['cost'].append(heuristics['cpu-pricereason'][app][threads][vm]['ovcost'])
                data['both-pricereason']['perf'].append(heuristics['both-pricereason'][app][threads][vm]['ovperf'])
                data['both-pricereason']['cost'].append(heuristics['both-pricereason'][app][threads][vm]['ovcost'])
                data['topdown-pricereason']['perf'].append(heuristics['topdown-pricereason'][app][threads][vm]['ovperf'])
                data['topdown-pricereason']['cost'].append(heuristics['topdown-pricereason'][app][threads][vm]['ovcost'])

plt.errorbar(scipy.stats.mstats.gmean(data['cpu-pricereason']['cost']), 
        scipy.stats.mstats.gmean(data['cpu-pricereason']['perf']),
        yerr=mean_confidence_interval(data['cpu-pricereason']['perf']),
        xerr=mean_confidence_interval(data['cpu-pricereason']['cost']), 
        c=colors[5], alpha=0.5, label=heuristic_name['cpu-pricereason'], fmt='o')
plt.errorbar(scipy.stats.mstats.gmean(data['both-pricereason']['cost']), 
        scipy.stats.mstats.gmean(data['both-pricereason']['perf']),
        yerr=mean_confidence_interval(data['both-pricereason']['perf']),
        xerr=mean_confidence_interval(data['both-pricereason']['cost']), 
        c=colors[6], alpha=0.5, label=heuristic_name['both-pricereason'], fmt='o')
plt.errorbar(scipy.stats.mstats.gmean(data['topdown-pricereason']['cost']), 
        scipy.stats.mstats.gmean(data['topdown-pricereason']['perf']),
        yerr=mean_confidence_interval(data['topdown-pricereason']['perf']),
        xerr=mean_confidence_interval(data['topdown-pricereason']['cost']), 
        c=colors[7], alpha=0.5, label=heuristic_name['topdown-pricereason'], fmt='o')

lgnd = plt.legend(loc='center right')
for i in lgnd.legendHandles:
    i._sizes = [10]
plt.ylabel("Performance Speedup")
plt.xlabel("Cost Reduction")
plt.hlines(1, 0.90, 1.1, color='#000')
plt.vlines(1, 0.8, 1.01, color='#000')
plt.xlim(0.95, 1.05)
plt.ylim(0.875, 1.01)
plt.xticks([0.95, 1.00, 1.05])
plt.yticks([0.9, 0.95, 1.00])
plt.savefig(GRAPHS_DIR+'/'+'heuristics-mean-pr-cpu-notchanges.svg', dpi=100,
            bbox_inches='tight', format='svg', pad_inches = 0)
plt.show()
plt.clf()
