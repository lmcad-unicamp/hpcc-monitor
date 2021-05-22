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
FILE_CONS = 'results/exp.nocons.json'
FILE = 'results/exp.json'
with open(FILE, 'r') as fp:
    heuristics = json.load(fp)
with open(FILE_CONS, 'r') as fp:
    heuristics_cons = json.load(fp)
GRAPHS_DIR = 'graphs'
if not os.path.exists(GRAPHS_DIR):
    os.makedirs(GRAPHS_DIR)

data = {}
for heuristic in price_heuristics:
    data[heuristic] = {}
    for app in heuristics[heuristic]:
        data[heuristic][app] = {}
        if not app in heuristics_cons[heuristic]:
            print("ERRO1", heuristic, app)
            continue
        for threads in heuristics[heuristic][app]:
            if not threads in heuristics_cons[heuristic][app]:
                print("ERRO2", heuristic, app, threads)
                continue
            for vm in heuristics[heuristic][app][threads]:
                if heuristics[heuristic][app][threads][vm]['current']['experiment']:
                    if not vm in heuristics_cons[heuristic][app][threads]:
                        print("ERRO3", heuristic, app, threads, vm)
                        continue
                    elif vm == heuristics[heuristic][app][threads][vm]['selected']['instance']['name']:
                        if vm != heuristics_cons[heuristic][app][threads][vm]['selected']['instance']['name']:
                            if not threads in data[heuristic][app]:
                                data[heuristic][app][threads] = {}
                            if not vm in data[heuristic][app][threads]:
                                data[heuristic][app][threads][vm] = {}

                            data[heuristic][app][threads][vm]['hperf'] = heuristics[heuristic][app][threads][vm]['ovperf']
                            data[heuristic][app][threads][vm]['hcost'] = heuristics[heuristic][app][threads][vm]['ovcost']
                            data[heuristic][app][threads][vm]['hcperf'] = heuristics_cons[heuristic][app][threads][vm]['ovperf']
                            data[heuristic][app][threads][vm]['hccost'] = heuristics_cons[heuristic][app][threads][vm]['ovcost']

results = {}
for heuristic in price_heuristics:
    results[heuristic] = {'hperf': [], 'hcost': [], 'hcperf': [], 'hccost': []}
    for app in data[heuristic]:
        for threads in data[heuristic][app]:
            for vm in data[heuristic][app][threads]:
                results[heuristic]['hperf'].append(data[heuristic][app][threads][vm]['hperf'])
                results[heuristic]['hcost'].append(data[heuristic][app][threads][vm]['hcost'])
                results[heuristic]['hcperf'].append(data[heuristic][app][threads][vm]['hcperf'])
                results[heuristic]['hccost'].append(data[heuristic][app][threads][vm]['hccost'])

markers_heuristics=["*","d",7,6]
alpha_heuristics=[1, 0.3, 0.3, 0.3]
sizes_heuristics=[60, 40, 40, 40]
plt.figure(figsize=(6.4, 3.5))
for h,c in zip(results, colors):
    if h == 'vcpu':
        plt.scatter(results[h]['hccost'], results[h]['hcperf'], c=c, marker='o',
            edgecolor='black', linewidth=0.5, alpha=0.8, label=heuristic_name[h])
    elif results[h]['hccost']:
        plt.errorbar(scipy.stats.mstats.gmean(results[h]['hccost']), 
            scipy.stats.mstats.gmean(results[h]['hcperf']),
            yerr=mean_confidence_interval(results[h]['hcperf']),
            xerr=mean_confidence_interval(results[h]['hccost']), 
            c=c, alpha=0.5, label=heuristic_name[h], fmt='o')

lgnd = plt.legend(loc='upper left', ncol=1, facecolor='white', frameon=True)
for i in lgnd.legendHandles:
    i._sizes = [10]
plt.ylabel("Performance Speedup")
plt.xlabel("Cost Reduction")
plt.hlines(1, 0.4, 1.3, color='#000')
plt.vlines(1, 0.4, 1.8, color='#000')
plt.xlim(0.4, 1.3)
plt.ylim(0.4, 1.8)
#plt.xticks([0.70, 0.80, 0.90, 1.00, 1.10])
plt.savefig(GRAPHS_DIR+'/'+'conservatism-means.svg', dpi=100,
            bbox_inches='tight', format='svg', pad_inches = 0)
plt.show()
plt.clf()

for h,c in zip(results, colors):
    if results[h]['hccost']:
        plt.scatter(results[h]['hccost'], results[h]['hcperf'], c=c, marker='o',
            edgecolor='black', linewidth=0.5, alpha=1, label=h)
lgnd = plt.legend(loc='upper left', facecolor='white', frameon=True)
for i in lgnd.legendHandles:
    i._sizes = [50]
plt.ylabel("Performance Speedup")
plt.xlabel("Cost Reduction")
plt.hlines(1, 0.4, 4, color='#000')
plt.vlines(1, 0, 5.5, color='#000')
plt.xlim(0.4, 4)
plt.ylim(0, 5.5)
plt.savefig(GRAPHS_DIR+'/'+'conservatism-selections.svg', dpi=100,
            bbox_inches='tight', format='svg', pad_inches = 0)
plt.show()
plt.clf()



# price-per-vcPU experiment2

data = {}
for heuristic in pricereason_heuristics:
    data[heuristic] = {}
    for app in heuristics[heuristic]:
        data[heuristic][app] = {}
        if not app in heuristics_cons[heuristic]:
            print("ERRO1", heuristic, app)
            continue
        for threads in heuristics[heuristic][app]:
            if not threads in heuristics_cons[heuristic][app]:
                print("ERRO2", heuristic, app, threads)
                continue
            for vm in heuristics[heuristic][app][threads]:
                if heuristics[heuristic][app][threads][vm]['current']['experiment']:
                    if not vm in heuristics_cons[heuristic][app][threads]:
                        print("ERRO3", heuristic, app, threads, vm)
                        continue
                    elif vm == heuristics[heuristic][app][threads][vm]['selected']['instance']['name']:
                        if vm != heuristics_cons[heuristic][app][threads][vm]['selected']['instance']['name']:
                            if not threads in data[heuristic][app]:
                                data[heuristic][app][threads] = {}
                            if not vm in data[heuristic][app][threads]:
                                data[heuristic][app][threads][vm] = {}

                            data[heuristic][app][threads][vm]['hperf'] = heuristics[heuristic][app][threads][vm]['ovperf']
                            data[heuristic][app][threads][vm]['hcost'] = heuristics[heuristic][app][threads][vm]['ovcost']
                            data[heuristic][app][threads][vm]['hcperf'] = heuristics_cons[heuristic][app][threads][vm]['ovperf']
                            data[heuristic][app][threads][vm]['hccost'] = heuristics_cons[heuristic][app][threads][vm]['ovcost']

results = {}
plt.figure(figsize=(6.4, 3.5))
for heuristic in pricereason_heuristics:
    results[heuristic] = {'hperf': [], 'hcost': [], 'hcperf': [], 'hccost': []}
    for app in data[heuristic]:
        for threads in data[heuristic][app]:
            for vm in data[heuristic][app][threads]:
                results[heuristic]['hperf'].append(data[heuristic][app][threads][vm]['hperf'])
                results[heuristic]['hcost'].append(data[heuristic][app][threads][vm]['hcost'])
                results[heuristic]['hcperf'].append(data[heuristic][app][threads][vm]['hcperf'])
                results[heuristic]['hccost'].append(data[heuristic][app][threads][vm]['hccost'])

markers_heuristics=["*","d",7,6]
alpha_heuristics=[1, 0.3, 0.3, 0.3]
sizes_heuristics=[60, 40, 40, 40]
for h,c in zip(results, colors[4:]):
        if results[h]['hccost']:
            plt.errorbar(scipy.stats.mstats.gmean(results[h]['hccost']), 
                scipy.stats.mstats.gmean(results[h]['hcperf']),
                yerr=mean_confidence_interval(results[h]['hcperf']),
                xerr=mean_confidence_interval(results[h]['hccost']), 
                c=c, alpha=0.5, label=heuristic_name[h], fmt='o')

lgnd = plt.legend(loc='lower left', ncol=1, facecolor='white', frameon=True)
for i in lgnd.legendHandles:
    i._sizes = [10]
plt.ylabel("Performance Speedup")
plt.xlabel("Cost Reduction")
plt.hlines(1, 0.9, 2.2, color='#000')
plt.vlines(1, 0.4, 1.3, color='#000')
plt.xlim(0.9, 2.2)
plt.ylim(0.4, 1.3)
plt.savefig(GRAPHS_DIR+'/'+'conservatism-means-pr.svg', dpi=100,
            bbox_inches='tight', format='svg', pad_inches = 0)
plt.show()
plt.clf()

for h,c in zip(results, colors[4:]):
    if results[h]['hccost']:
        plt.scatter(results[h]['hccost'], results[h]['hcperf'], c=c, marker='o',
            edgecolor='black', linewidth=0.5, alpha=1, label=h)
lgnd = plt.legend(loc='upper right', facecolor='white', frameon=True)
for i in lgnd.legendHandles:
    i._sizes = [50]
plt.ylabel("Performance Speedup")
plt.xlabel("Cost Reduction")
plt.hlines(1, 0.4, 1.7, color='#000')
plt.vlines(1, 0.5, 2.5, color='#000')
plt.xlim(0.4, 1.7)
plt.ylim(0.5, 2.5)
plt.savefig(GRAPHS_DIR+'/'+'conservatism-selections-pr.svg', dpi=100,
            bbox_inches='tight', format='svg', pad_inches = 0)
plt.show()
plt.clf()


