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

heuristicsnumber = {'vcpu': 'h5', 'cpu': 'h6', 'both': 'h7', 'topdown': 'h8',
                    'vcpu-pricereason': 'h5', 'cpu-pricereason': 'h6', 
                    'both-pricereason': 'h7', 'topdown-pricereason': 'h8'}

#------------------------------------ price
FILE = 'results/exp2.json'
with open(FILE, 'r') as fp:
    heuristics = json.load(fp)
GRAPHS_DIR = 'graphs'
if not os.path.exists(GRAPHS_DIR):
    os.makedirs(GRAPHS_DIR)

data = {}
for heuristic in price_heuristics:
    for app in heuristics[heuristic]:
        for threads in heuristics[heuristic][app]:
            for vm in heuristics[heuristic][app][threads]:
                if heuristics[heuristic][app][threads][vm]['current']['experiment']:
                    if vm != heuristics[heuristic][app][threads][vm]['selected']['instance']['name']:
                        tupl = (heuristics[heuristic][app][threads][vm]['ovcost'], heuristics[heuristic][app][threads][vm]['ovperf'])
                        if tupl not in data:
                            data[tupl] = {}
                            data[tupl]['total'] = 0
                        if heuristic not in data[tupl]:
                            data[tupl][heuristicsnumber[heuristic]] = 0
                        data[tupl][heuristicsnumber[heuristic]] = data[tupl][heuristicsnumber[heuristic]] + 1
                        if heuristic != 'topdown':
                            data[tupl]['total'] = data[tupl]['total'] + 1

x={'h5':[], 'h6':[], 'h7':[], 'h8':[], 'h5-h6':[], 'h5-h7':[], 'h6-h7':[], 'h5-h6-h7':[]}
y={'h5':[], 'h6':[], 'h7':[], 'h8':[], 'h5-h6':[], 'h5-h7':[], 'h6-h7':[], 'h5-h6-h7':[]}
sizes={'h5':[], 'h6':[], 'h7':[], 'h8':[], 'h5-h6':[], 'h5-h7':[], 'h6-h7':[], 'h5-h6-h7':[]}
fig = plt.figure(figsize=(6.4, 3.5))
for d in data:
    hs = '-'.join(sorted([da for da in data[d] if da != 'total']))
    if hs.find("h8") != -1:
        x['h8'].append(d[0])
        y['h8'].append(d[1])
        sizes['h8'].append(data[d]['h8']*50)
        hs = re.sub('-?h8', '', hs)
    if hs:
        if hs == "h5":
            x['h5'].append(d[0])
            y['h5'].append(d[1])
            sizes['h5'].append(data[d]['total']*50)
        elif hs == "h6":
            x['h6'].append(d[0])
            y['h6'].append(d[1])
            sizes['h6'].append(data[d]['total']*50)
        elif hs == "h7":
            x['h7'].append(d[0])
            y['h7'].append(d[1])
            sizes['h7'].append(data[d]['total']*50)
        elif hs == "h5-h6":
            x['h5-h6'].append(d[0])
            y['h5-h6'].append(d[1])
            sizes['h5-h6'].append(data[d]['total']*50)
        elif hs == "h5-h7":
            x['h5-h7'].append(d[0])
            y['h5-h7'].append(d[1])
            sizes['h5-h7'].append(data[d]['total']*50)
        elif hs == "h6-h7":
            x['h6-h7'].append(d[0])
            y['h6-h7'].append(d[1])
            sizes['h6-h7'].append(data[d]['total']*50)
        elif hs == "h5-h6-h7":
            x['h5-h6-h7'].append(d[0])
            y['h5-h6-h7'].append(d[1])
            sizes['h5-h6-h7'].append(data[d]['total']*50)
p = 0
if x['h5']:
    p+=1
    plt.scatter(x['h5'], y['h5'], s=sizes['h5'], c='#FF0000', marker='o',
            edgecolor='black', linewidth=0.5, alpha=1, label='vCPU-')
if x['h6']:
    p+=1
    plt.scatter(x['h6'], y['h6'], s=sizes['h6'], c='#0000FF', marker='o',
            edgecolor='black', linewidth=0.5, alpha=1, label='core-')
if x['h7']:
    p+=1
    plt.scatter(x['h7'], y['h7'], s=sizes['h7'], c='#FFFF00', marker='o',
            edgecolor='black', linewidth=0.5, alpha=1, label='hybrid-')
if x['h5-h6']:
    p+=1
    plt.scatter(x['h5-h6'], y['h5-h6'], s=sizes['h5-h6'], c='#6600FF', marker='o',
            edgecolor='black', linewidth=0.5, alpha=1, label='vCPU- and core-')
if x['h5-h7']:
    p+=1
    #FF6600
    plt.scatter(x['h5-h7'], y['h5-h7'], s=sizes['h5-h7'], c='#FFFF00', marker='o',
            edgecolor='black', linewidth=0.5, alpha=1, label='vCPU- and hybrid-')
if x['h6-h7']:
    p+=1
    plt.scatter(x['h6-h7'], y['h6-h7'], s=sizes['h6-h7'], c='#00FF00', marker='o',
            edgecolor='black', linewidth=0.5, alpha=1, label='core- and hybrid-')
if x['h5-h6-h7']:
    p+=1
    plt.scatter(x['h5-h6-h7'], y['h5-h6-h7'], s=sizes['h5-h6-h7'], c='#5c5c5c', marker='o',
            edgecolor='black', linewidth=0.5, alpha=1, label='vCPU- and core- and hybrid-')
if x['h8']:
    p+=1
    #e30079
    plt.scatter(x['h8'], y['h8'], s=sizes['h8'], c='#0000FF', marker='x', 
            linewidth=0.7, alpha=1, label='top-down-')

lgnd = plt.legend(loc='upper left', facecolor='white', frameon=True)
for i in lgnd.legendHandles:
    i._sizes = [50]
plt.ylabel("Performance Speedup")
plt.xlabel("Cost Reduction")
plt.hlines(1, 0.2, 3, color='#000')
plt.vlines(1, 0.0, 4.5, color='#000')
plt.xlim(0.2, 3)
plt.ylim(0.1, 2)
#plt.yticks([0.25, 0.50, 0.75, 1, 1.25, 1.5, 1.75, 2])
plt.savefig(GRAPHS_DIR+'/'+'heuristics-selections.svg', dpi=100,
            bbox_inches='tight', format='svg', pad_inches = 0)
plt.show()
plt.clf()






fig, ax = plt.subplots()

data = {}
for heuristic in price_heuristics:
    data[heuristic] = {}
    data[heuristic]['perf'] = []
    data[heuristic]['cost'] = []
    for app in heuristics[heuristic]:
        for threads in heuristics[heuristic][app]:
            for vm in heuristics[heuristic][app][threads]:
                if heuristics[heuristic][app][threads][vm]['current']['experiment']:
                    if vm != heuristics[heuristic][app][threads][vm]['selected']['instance']['name']:
                        data[heuristic]['perf'].append(heuristics[heuristic][app][threads][vm]['ovperf'])
                        data[heuristic]['cost'].append(heuristics[heuristic][app][threads][vm]['ovcost'])
pprint(data)
for h,c in zip(data, colors):
    ax.scatter(scipy.stats.mstats.gmean(data[h]['cost']), 
                scipy.stats.mstats.gmean(data[h]['perf']),
                c=c, alpha=0.5, marker='o')
    ax.scatter(scipy.stats.mstats.gmean(data[h]['cost']),
                max(data[h]['perf']),
                c=c, alpha=0.5, marker='x')
    ax.scatter(scipy.stats.mstats.gmean(data[h]['cost']),
                min(data[h]['perf']),
                c=c, alpha=0.5, marker='x')
    ax.scatter(max(data[h]['cost']),
                scipy.stats.mstats.gmean(data[h]['perf']),
                c=c, alpha=0.5, marker='x')
    ax.scatter(min(data[h]['cost']),
                scipy.stats.mstats.gmean(data[h]['perf']),
                c=c, alpha=0.5, marker='x')

handles = [f("o", colors[i]) for i in range(4)]
labels = [heuristic_name[h] for h in price_heuristics]
plt.legend(handles=handles, labels=labels, loc='lower right', facecolor='white', frameon=True)

axins = ax.inset_axes([.6, 0.7, 0.7, 0.5])
for h,c in zip(data, colors):
    axins.errorbar(scipy.stats.mstats.gmean(data[h]['cost']), 
                scipy.stats.mstats.gmean(data[h]['perf']),
                yerr=mean_confidence_interval(data[h]['perf']),
                xerr=mean_confidence_interval(data[h]['cost']), 
                c=c, alpha=0.5, fmt='o')
axins.set_xlim(0.99, 1.7)
axins.set_ylim(0.65, 1.20)
axins.hlines(1, 0.99, 1.7, color='#000')
axins.vlines(1, 0.65, 1.20, color='#000')
axins.hlines(0.65, 0.99, 1.7, color='#000')
axins.hlines(1.20, 0.99, 1.7, color='#000')
axins.vlines(0.99, 0.65, 1.20, color='#000')
axins.vlines(1.7, 0.65, 1.20, color='#000')
axins.set_yticks([0.70, 0.80, 0.90, 1.00, 1.10, 1.20])

ax.indicate_inset_zoom(axins)

plt.ylabel("Performance Speedup")
plt.xlabel("Cost Reduction")
plt.hlines(1, 0.0, 4.5, color='#000')
plt.vlines(1, 0.0, 4.5, color='#000')
plt.xlim(0.3, 3.0)
plt.ylim(0.25, 1.75)
plt.savefig(GRAPHS_DIR+'/'+'heuristics-mean.svg', dpi=100, 
            bbox_inches='tight', format='svg', pad_inches = 0)
plt.show()
plt.clf()

#------------------------------------ price-reason

data = {}
for heuristic in pricereason_heuristics:
    for app in heuristics[heuristic]:
        for threads in heuristics[heuristic][app]:
            for vm in heuristics[heuristic][app][threads]:
                if heuristics[heuristic][app][threads][vm]['current']['experiment']:
                    if vm != heuristics[heuristic][app][threads][vm]['selected']['instance']['name']:
                        tupl = (heuristics[heuristic][app][threads][vm]['ovcost'], heuristics[heuristic][app][threads][vm]['ovperf'])
                        if tupl not in data:
                            data[tupl] = {}
                            data[tupl]['total'] = 0
                        if heuristic not in data[tupl]:
                            data[tupl][heuristicsnumber[heuristic]] = 0
                        data[tupl][heuristicsnumber[heuristic]] = data[tupl][heuristicsnumber[heuristic]] + 1
                        if heuristic != 'topdown':
                            data[tupl]['total'] = data[tupl]['total'] + 1

x={'h5':[], 'h6':[], 'h7':[], 'h8':[], 'h5-h6':[], 'h5-h7':[], 'h6-h7':[], 'h5-h6-h7':[]}
y={'h5':[], 'h6':[], 'h7':[], 'h8':[], 'h5-h6':[], 'h5-h7':[], 'h6-h7':[], 'h5-h6-h7':[]}
sizes={'h5':[], 'h6':[], 'h7':[], 'h8':[], 'h5-h6':[], 'h5-h7':[], 'h6-h7':[], 'h5-h6-h7':[]}
fig = plt.figure(figsize=(6.4, 3.5))
for d in data:
    hs = '-'.join(sorted([da for da in data[d] if da != 'total']))
    if hs.find("h8") != -1:
        x['h8'].append(d[0])
        y['h8'].append(d[1])
        sizes['h8'].append(data[d]['h8']*50)
        hs = re.sub('-?h8', '', hs)
    if hs:
        if hs == "h5":
            x['h5'].append(d[0])
            y['h5'].append(d[1])
            sizes['h5'].append(data[d]['total']*50)
        elif hs == "h6":
            x['h6'].append(d[0])
            y['h6'].append(d[1])
            sizes['h6'].append(data[d]['total']*50)
        elif hs == "h7":
            x['h7'].append(d[0])
            y['h7'].append(d[1])
            sizes['h7'].append(data[d]['total']*50)
        elif hs == "h5-h6":
            x['h5-h6'].append(d[0])
            y['h5-h6'].append(d[1])
            sizes['h5-h6'].append(data[d]['total']*50)
        elif hs == "h5-h7":
            x['h5-h7'].append(d[0])
            y['h5-h7'].append(d[1])
            sizes['h5-h7'].append(data[d]['total']*50)
        elif hs == "h6-h7":
            x['h6-h7'].append(d[0])
            y['h6-h7'].append(d[1])
            sizes['h6-h7'].append(data[d]['total']*50)
        elif hs == "h5-h6-h7":
            x['h5-h6-h7'].append(d[0])
            y['h5-h6-h7'].append(d[1])
            sizes['h5-h6-h7'].append(data[d]['total']*50)
p = 0
if x['h5']:
    p+=1
    plt.scatter(x['h5'], y['h5'], s=sizes['h5'], c='#FF0000', marker='o',
            edgecolor='black', linewidth=0.5, alpha=1, label='vCPU-ppv-')
if x['h6']:
    p+=1
    plt.scatter(x['h6'], y['h6'], s=sizes['h6'], c='#0000FF', marker='o',
            edgecolor='black', linewidth=0.5, alpha=1, label='core-ppv-')
if x['h7']:
    p+=1
    plt.scatter(x['h7'], y['h7'], s=sizes['h7'], c='#FFFF00', marker='o',
            edgecolor='black', linewidth=0.5, alpha=1, label='hybrid-ppv-')
if x['h5-h6']:
    p+=1
    plt.scatter(x['h5-h6'], y['h5-h6'], s=sizes['h5-h6'], c='#6600FF', marker='o',
            edgecolor='black', linewidth=0.5, alpha=1, label='vCPU-ppv- and core-ppv-')
if x['h6-h7']:
    p+=1
    plt.scatter(x['h6-h7'], y['h6-h7'], s=sizes['h6-h7'], c='#00FF00', marker='o',
            edgecolor='black', linewidth=0.5, alpha=1, label='core-ppv- and hybrid-ppv-')
if x['h5-h7']:
    p+=1
    #FF6600
    plt.scatter(x['h5-h7'], y['h5-h7'], s=sizes['h5-h7'], c='#FFFF00', marker='o',
            edgecolor='black', linewidth=0.5, alpha=1, label='vCPU-ppv- and hybrid-ppv-')
if x['h5-h6-h7']:
    p+=1
    plt.scatter(x['h5-h6-h7'], y['h5-h6-h7'], s=sizes['h5-h6-h7'], c='#5c5c5c', marker='o',
            edgecolor='black', linewidth=0.5, alpha=1, label='vCPU-ppv- and core-ppv- and hybrid-ppv-')
if x['h8']:
    p+=1
    #e30079
    plt.scatter(x['h8'], y['h8'], s=sizes['h8'], c='#0000FF', marker='x', 
            linewidth=0.7, alpha=1, label='top-down-ppv-')

lgnd = plt.legend(loc='upper left', facecolor='white', frameon=True)
for i in lgnd.legendHandles:
    i._sizes = [50]
#lgnd.get_frame().set_linewidth(100)
plt.ylabel("Performance Speedup")
plt.xlabel("Cost Reduction")
plt.hlines(1, 0.0, 4, color='#000')
plt.vlines(1, 0.0, 6, color='#000')
plt.xlim(0.0, 4)
plt.ylim(0.0, 6)
plt.savefig(GRAPHS_DIR+'/'+'heuristics-pr-selections.svg', dpi=100,
            bbox_inches='tight', format='svg', pad_inches = 0)
plt.show()
plt.clf()






fig, ax = plt.subplots()

data = {}
for heuristic in pricereason_heuristics:
    data[heuristic] = {}
    data[heuristic]['perf'] = []
    data[heuristic]['cost'] = []
    for app in heuristics[heuristic]:
        for threads in heuristics[heuristic][app]:
            for vm in heuristics[heuristic][app][threads]:
                if heuristics[heuristic][app][threads][vm]['current']['experiment']:
                    if vm != heuristics[heuristic][app][threads][vm]['selected']['instance']['name']:
                        data[heuristic]['perf'].append(heuristics[heuristic][app][threads][vm]['ovperf'])
                        data[heuristic]['cost'].append(heuristics[heuristic][app][threads][vm]['ovcost'])

for h,c in zip(data, colors[4:]):
    ax.scatter(scipy.stats.mstats.gmean(data[h]['cost']), 
                scipy.stats.mstats.gmean(data[h]['perf']),
                c=c, alpha=0.5, marker='o')
    ax.scatter(scipy.stats.mstats.gmean(data[h]['cost']),
                max(data[h]['perf']),
                c=c, alpha=0.5, marker='x')
    ax.scatter(scipy.stats.mstats.gmean(data[h]['cost']),
                min(data[h]['perf']),
                c=c, alpha=0.5, marker='x')
    ax.scatter(max(data[h]['cost']),
                scipy.stats.mstats.gmean(data[h]['perf']),
                c=c, alpha=0.5, marker='x')
    ax.scatter(min(data[h]['cost']),
                scipy.stats.mstats.gmean(data[h]['perf']),
                c=c, alpha=0.5, marker='x')

handles = [f("o", colors[i+4]) for i in range(4)]
labels = [heuristic_name[h] for h in pricereason_heuristics]
plt.legend(handles=handles, labels=labels, loc='upper left', facecolor='white', frameon=True)

axins = ax.inset_axes([.5, 0.6, 0.7, 0.5])
for h,c in zip(data, colors[4:]):
    axins.errorbar(scipy.stats.mstats.gmean(data[h]['cost']), 
                scipy.stats.mstats.gmean(data[h]['perf']),
                yerr=mean_confidence_interval(data[h]['perf']),
                xerr=mean_confidence_interval(data[h]['cost']), 
                c=c, alpha=0.5, fmt='o')
axins.set_xlim(0.99, 1.5)
axins.set_ylim(0.65, 1.4)
axins.hlines(1, 0.99, 1.5, color='#000')
axins.vlines(1, 0.65, 1.4, color='#000')
axins.hlines(0.65, 0.99, 1.5, color='#000')
axins.hlines(1.4, 0.99, 1.5, color='#000')
axins.vlines(0.99, 0.65, 1.4, color='#000')
axins.vlines(1.5, 0.65, 1.4, color='#000')
axins.set_yticks([0.70, 0.80, 0.90, 1.00, 1.10, 1.20, 1.30])

ax.indicate_inset_zoom(axins)

plt.ylabel("Performance Speedup")
plt.xlabel("Cost Reduction")
plt.hlines(1, 0.0, 4, color='#000')
plt.vlines(1, 0.0, 6, color='#000')
plt.xlim(0.0, 4)
plt.ylim(0.0, 6)

plt.savefig(GRAPHS_DIR+'/'+'heuristics-mean-pr.svg', dpi=100, 
            bbox_inches='tight', format='svg', pad_inches = 0)
plt.show()
plt.clf()