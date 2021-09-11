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

#------------------------------------ experiment 2
FILE = 'results/exp2.json'
with open(FILE, 'r') as fp:
    heuristics = json.load(fp)
GRAPHS_DIR = 'graphs'
if not os.path.exists(GRAPHS_DIR):
    os.makedirs(GRAPHS_DIR)

data = {}
heuristicsnumber = {'vcpu': 'h1', 'cpu': 'h2', 'both': 'h3', 'topdown': 'h4',
                'vcpu-pricereason': 'h5', 'cpu-pricereason': 'h6', 
                'both-pricereason': 'h7', 'topdown-pricereason': 'h8'}


limits = {'vcpu': [0.3, 4.5, 0.2, 1.75],
        'cpu': [0.3, 3.6, 0.0, 3.5],
        'both': [0.3, 3.6, 0.0, 3.5],
        'topdown': [0.3, 3.6, 0.0, 3.5]}
data = {}
for heuristic in price_heuristics:
    heuris = heuristicsnumber[heuristic]
    heuristic2=heuristic+'-pricereason'
    heuris2 = heuristicsnumber[heuristic2]
    data[heuris] = {}
    data[heuris2] = {}
    for app in heuristics[heuristic]:
        for threads in heuristics[heuristic][app]:
            for vm in heuristics[heuristic][app][threads]:
                if heuristics[heuristic][app][threads][vm]['current']['experiment']:
                    if vm != heuristics[heuristic][app][threads][vm]['selected']['instance']['name']:
                        tupl = (heuristics[heuristic][app][threads][vm]['ovcost'], heuristics[heuristic][app][threads][vm]['ovperf'])
                        if tupl not in data[heuris]:
                            data[heuris][tupl] = 0
                        data[heuris][tupl] = data[heuris][tupl] + 1
                    if vm != heuristics[heuristic2][app][threads][vm]['selected']['instance']['name']:
                        tupl = (heuristics[heuristic2][app][threads][vm]['ovcost'], heuristics[heuristic2][app][threads][vm]['ovperf'])
                        if tupl not in data[heuris2]:
                            data[heuris2][tupl] = 0
                        data[heuris2][tupl] = data[heuris2][tupl] + 1
    x={heuris:[], heuris2:[]}
    y={heuris:[], heuris2:[]}
    sizes={heuris:[], heuris2:[]}
    for d in data[heuris]:
        x[heuris].append(d[0])
        y[heuris].append(d[1])
        sizes[heuris].append(data[heuris][d]*50)
    for d in data[heuris2]:
        x[heuris2].append(d[0])
        y[heuris2].append(d[1])
        sizes[heuris2].append(data[heuris2][d]*50)
    plt.style.use('seaborn')
    plt.scatter(x[heuris], y[heuris], s=sizes[heuris], c='#FF0000', marker='o',
            edgecolor='black', linewidth=0.5, alpha=0.8, label=heuristic_name[heuristic])
    plt.scatter(x[heuris2], y[heuris2], s=sizes[heuris2], c='#0000FF', marker='x',
            edgecolor='black', linewidth=1, alpha=0.8, label=heuristic_name[heuristic2])
        

    lgnd = plt.legend(loc='lower right', ncol=1, fontsize=12, facecolor='white', frameon=True)
    for i in lgnd.legendHandles:
        i._sizes = [50]
    plt.ylabel("Performance Speedup", fontsize=12)
    plt.xlabel("Cost Reduction", fontsize=12)
    plt.hlines(1, limits[heuristic][0], limits[heuristic][1], color='#000')
    plt.vlines(1, limits[heuristic][2], limits[heuristic][3], color='#000')
    plt.xlim(limits[heuristic][0], limits[heuristic][1])
    plt.ylim(limits[heuristic][2], limits[heuristic][3])
    plt.yticks(fontsize=12)
    plt.xticks(fontsize=12)

    plt.savefig(GRAPHS_DIR+'/'+'heuristic-pr-comparison-'+heuristic+'.svg', dpi=100, 
        bbox_inches='tight', format='svg', pad_inches = 0)
    plt.show()
    plt.clf()


data = {}
plt.figure(figsize=(6.4, 3.5))
for heuristic in heuristics:
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

for h,c in zip(data, colors):
        plt.errorbar(scipy.stats.mstats.gmean(data[h]['cost']), 
                scipy.stats.mstats.gmean(data[h]['perf']),
                yerr=mean_confidence_interval(data[h]['perf']),
                xerr=mean_confidence_interval(data[h]['cost']), 
                c=c, alpha=0.5, label=heuristic_name[h], fmt='o')

lgnd = plt.legend(loc='upper right', ncol=2, facecolor='white', frameon=True)
for i in lgnd.legendHandles:
    i._sizes = [10]
plt.ylabel("Performance Speedup")
plt.xlabel("Cost Reduction")
plt.hlines(1, 0.99, 1.7, color='#000')
plt.vlines(1, 0.6, 1.5, color='#000')
plt.xlim(0.99, 1.7)
plt.ylim(0.69, 1.45)
plt.savefig(GRAPHS_DIR+'/'+'exp2-heuristics-prxp-mean-onlychanges.svg', dpi=100,
            bbox_inches='tight', format='svg', pad_inches = 0)
plt.show()
plt.clf()



#------------------------------------ experiment 1
FILE = 'results/exp1.json'
with open(FILE, 'r') as fp:
    heuristics = json.load(fp)

data = {}
plt.figure(figsize=(6.4, 3.5))
for heuristic in heuristics:
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

for h,c in zip(data, colors):
        print(h, scipy.stats.mstats.gmean(data[h]['cost']), scipy.stats.mstats.gmean(data[h]['perf']))
        plt.errorbar(scipy.stats.mstats.gmean(data[h]['cost']), 
                scipy.stats.mstats.gmean(data[h]['perf']),
                yerr=mean_confidence_interval(data[h]['perf']),
                xerr=mean_confidence_interval(data[h]['cost']), 
                c=c, alpha=0.5, label=heuristic_name[h], fmt='o')

lgnd = plt.legend(loc='lower left', ncol=1, facecolor='white', frameon=True)
for i in lgnd.legendHandles:
    i._sizes = [10]
plt.ylabel("Performance Speedup")
plt.xlabel("Cost Reduction")
plt.hlines(1, 0.99, 3.6, color='#000')
plt.vlines(1, 0.49, 1.1, color='#000')
plt.xlim(0.99, 3.6)
plt.ylim(0.49, 1.1)
plt.annotate('1', xy=(2.9, 0.88),  xycoords='data',
            xytext=(2.8, .85), textcoords='data',
            arrowprops=dict(facecolor='black', width=1, headlength=6, headwidth=7),
            horizontalalignment='right', verticalalignment='top')
plt.annotate('2', xy=(2.93, 0.97),  xycoords='data',
            xytext=(2.8, 1.05), textcoords='data',
            arrowprops=dict(facecolor='black', width=1, headlength=6, headwidth=7),
            horizontalalignment='right', verticalalignment='top')
plt.savefig(GRAPHS_DIR+'/'+'exp1-heuristics-prxp-mean-onlychanges.svg', dpi=100,
            bbox_inches='tight', format='svg', pad_inches = 0)
plt.show()
plt.clf()