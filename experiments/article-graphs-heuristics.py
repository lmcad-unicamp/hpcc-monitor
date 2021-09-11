from experiments import scipy, json, np, os, re, heuristic_name, article_heuristics, sortedbyvcpu, INSTANCES 
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
FILE = 'results/exp1.json'
with open(FILE, 'r') as fp:
    heuristics = json.load(fp)
GRAPHS_DIR = 'graphs-article'
if not os.path.exists(GRAPHS_DIR):
    os.makedirs(GRAPHS_DIR)

data = {}
plt.figure(figsize=(6.4, 3.5))
for heuristic in article_heuristics:
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

lgnd = plt.legend(loc='upper left', ncol=1, facecolor='white', frameon=True)
for i in lgnd.legendHandles:
    i._sizes = [10]
plt.ylabel("Performance Speedup")
plt.xlabel("Cost Reduction")
plt.hlines(1, 0.99, 3.55, color='#000')
plt.vlines(1, 0.45, 1.1, color='#000')
plt.xlim(0.99, 3.55)
plt.ylim(0.45, 1.1)
plt.savefig(GRAPHS_DIR+'/'+'exp1-heuristics.svg', dpi=100,
            bbox_inches='tight', format='svg', pad_inches = 0)
plt.show()
plt.clf()



#------------------------------------ experiment 1
FILE = 'results/exp2.json'
with open(FILE, 'r') as fp:
    heuristics = json.load(fp)

data = {}
plt.figure(figsize=(6.4, 3.5))
for heuristic in article_heuristics:
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

lgnd = plt.legend(loc='lower left', ncol=1, facecolor='white', frameon=True)
for i in lgnd.legendHandles:
    i._sizes = [10]
plt.ylabel("Performance Speedup")
plt.xlabel("Cost Reduction")
plt.hlines(1, 0.99, 1.65, color='#000')
plt.vlines(1, 0.65, 1.35, color='#000')
plt.xlim(0.99, 1.65)
plt.ylim(0.65, 1.35)
plt.savefig(GRAPHS_DIR+'/'+'exp2-heuristics.svg', dpi=100,
            bbox_inches='tight', format='svg', pad_inches = 0)
plt.show()
plt.clf()