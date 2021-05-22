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


#------------------------------------ price
FILE = 'results/exp.json'
with open(FILE, 'r') as fp:
    heuristics = json.load(fp)
GRAPHS_DIR = 'graphs'
if not os.path.exists(GRAPHS_DIR):
    os.makedirs(GRAPHS_DIR)

data = {}
for heuristic in price_heuristics:
    data[heuristic] = {}
    for app in heuristics[heuristic]:
        for threads in heuristics[heuristic][app]:
            for vm in heuristics[heuristic][app][threads]:
                if heuristics[heuristic][app][threads][vm]['current']['experiment']:
                    if vm != heuristics[heuristic][app][threads][vm]['selected']['instance']['name']:
                        utilization = heuristics[heuristic][app][threads][vm]['current']['utilization']
                        utilization = round(utilization*100,2)
                        if utilization == 33.33:
                            print(heuristic, app, threads, vm)
                        if utilization not in data[heuristic]:
                            data[heuristic][utilization] = {}
                            data[heuristic][utilization]['name'] = utilization
                            data[heuristic][utilization]['perf'] = []
                            data[heuristic][utilization]['cost'] = []
                        data[heuristic][utilization]['perf'].append(heuristics[heuristic][app][threads][vm]['ovperf'])
                        data[heuristic][utilization]['cost'].append(heuristics[heuristic][app][threads][vm]['ovcost'])

markers_heuristics=["*","d",7,6]
alpha_heuristics=[1, 0.3, 0.3, 0.3]
sizes_heuristics=[60, 40, 40, 40]
labels = sorted([a for a in data[list(data.keys())[0]]])
for h,c,m,al,s in zip(data, colors, markers_heuristics, alpha_heuristics, sizes_heuristics):
    for a in data[h]:
        plt.scatter(a, scipy.stats.mstats.gmean(data[h][a]['perf']),
                    c=c, alpha=al, s=s, marker=m)


handles = [f(markers_heuristics[i], colors[i]) for i in range(4)]
labels = [heuristic_name[h] for h in price_heuristics]
lgnd = plt.legend(handles=handles, labels=labels, loc='lower right', facecolor='white', frameon=True)

for i in lgnd.legendHandles:
    i._sizes = [10]
plt.annotate('', xy=(32, 0.66),  xycoords='data',
            xytext=(28, 0.7), textcoords='data',
            arrowprops=dict(facecolor='black', width=3, headlength=6, headwidth=10),
            horizontalalignment='right', verticalalignment='top')
plt.ylabel("Performance Speedup")
plt.xlabel("vCPU utilization (%)")
plt.hlines(1, -.9, 100.5, color='#000')
plt.xlim(-0.9, 100.5)
plt.savefig(GRAPHS_DIR+'/'+'utilization-perf.svg', dpi=100, 
            bbox_inches='tight', format='svg', pad_inches = 0)
plt.show()
plt.clf()

markers_heuristics=["*","d",7,6]
alpha_heuristics=[1, 0.3, 0.3, 0.3]
sizes_heuristics=[60, 40, 40, 40]
fig = plt.figure(figsize=(6.4, 3.5))
labels = sorted([a for a in data[list(data.keys())[0]]])
for h,c,m,al,s in zip(data, colors, markers_heuristics, alpha_heuristics, sizes_heuristics):
    for a in data[h]:
        plt.scatter(a, scipy.stats.mstats.gmean(data[h][a]['cost']),
                    c=c, alpha=al, s=s, marker=m)


handles = [f(markers_heuristics[i], colors[i]) for i in range(4)]
labels = [heuristic_name[h] for h in price_heuristics]
lgnd = plt.legend(handles=handles, labels=labels, loc='upper right', facecolor='white', frameon=True)

for i in lgnd.legendHandles:
    i._sizes = [10]
plt.ylabel("Cost Reduction")
plt.xlabel("vCPU utilization (%)")
plt.hlines(1, -.9, 100.5, color='#000')
plt.xlim(-0.9, 100.5)
plt.savefig(GRAPHS_DIR+'/'+'utilization-cost.svg', dpi=100, 
            bbox_inches='tight', format='svg', pad_inches = 0)
plt.show()
plt.clf() 


#------------------------------------ price-reason

data = {}
for heuristic in pricereason_heuristics:
    data[heuristic] = {}
    for app in heuristics[heuristic]:
        for threads in heuristics[heuristic][app]:
            for vm in heuristics[heuristic][app][threads]:
                if heuristics[heuristic][app][threads][vm]['current']['experiment']:
                    if vm != heuristics[heuristic][app][threads][vm]['selected']['instance']['name']:
                        utilization = heuristics[heuristic][app][threads][vm]['current']['utilization']
                        utilization = round(utilization*100,2)
                        if utilization not in data[heuristic]:
                            data[heuristic][utilization] = {}
                            data[heuristic][utilization]['name'] = utilization
                            data[heuristic][utilization]['perf'] = []
                            data[heuristic][utilization]['cost'] = []
                        data[heuristic][utilization]['perf'].append(heuristics[heuristic][app][threads][vm]['ovperf'])
                        data[heuristic][utilization]['cost'].append(heuristics[heuristic][app][threads][vm]['ovcost'])


markers_heuristics=["*","d",7,6]
alpha_heuristics=[1, 0.3, 0.3, 0.3]
sizes_heuristics=[60, 40, 40, 40]
labels = sorted([a for a in data[list(data.keys())[0]]])
for h,c,m,al,s in zip(data, colors[4:], markers_heuristics, alpha_heuristics, sizes_heuristics):
    for a in data[h]:
        plt.scatter(a, scipy.stats.mstats.gmean(data[h][a]['perf']),
                    c=c, alpha=al, s=s, marker=m)


handles = [f(markers_heuristics[i], colors[i+4]) for i in range(4)]
labels = [heuristic_name[h] for h in pricereason_heuristics]
lgnd = plt.legend(handles=handles, labels=labels, loc='upper left', facecolor='white', frameon=True)

for i in lgnd.legendHandles:
    i._sizes = [10]
plt.ylabel("Performance Speedup")
plt.xlabel("vCPU utilization (%)")
plt.hlines(1, -.9, 100.5, color='#000')
plt.xlim(-0.9, 100.5)
plt.savefig(GRAPHS_DIR+'/'+'utilization-pr-perf.svg', dpi=100, 
            bbox_inches='tight', format='svg', pad_inches = 0)
plt.show()
plt.clf() 

markers_heuristics=["*","d",7,6]
alpha_heuristics=[1, 0.3, 0.3, 0.3]
sizes_heuristics=[60, 40, 40, 40]
fig = plt.figure(figsize=(6.4, 3.5))
labels = sorted([a for a in data[list(data.keys())[0]]])
for h,c,m,al,s in zip(data, colors[4:], markers_heuristics, alpha_heuristics, sizes_heuristics):
    for a in data[h]:
        plt.scatter(a, scipy.stats.mstats.gmean(data[h][a]['cost']),
                    c=c, alpha=al, s=s, marker=m)


handles = [f(markers_heuristics[i], colors[i+4]) for i in range(4)]
labels = [heuristic_name[h] for h in pricereason_heuristics]
lgnd = plt.legend(handles=handles, labels=labels, loc='upper right', facecolor='white', frameon=True)

for i in lgnd.legendHandles:
    i._sizes = [10]
plt.ylabel("Cost Reduction")
plt.xlabel("vCPU utilization (%)")
plt.hlines(1, -.9, 100.5, color='#000')
plt.xlim(-0.9, 100.5)
plt.savefig(GRAPHS_DIR+'/'+'utilization-pr-cost.svg', dpi=100, 
            bbox_inches='tight', format='svg', pad_inches = 0)
plt.show()
plt.clf() 