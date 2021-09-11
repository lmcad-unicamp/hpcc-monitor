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

#----------------------------------------------- price
FILE = 'results/exp.json'
with open(FILE, 'r') as fp:
    heuristics = json.load(fp)
GRAPHS_DIR = 'graphs-article'
if not os.path.exists(GRAPHS_DIR):
    os.makedirs(GRAPHS_DIR)

data = {}
for heuristic in article_heuristics:
    data[heuristic] = {'change': 0, 'nochange': 0}
    for app in heuristics[heuristic]:
        for threads in heuristics[heuristic][app]:
            for vm in heuristics[heuristic][app][threads]:
                if heuristics[heuristic][app][threads][vm]['current']['experiment']:
                    if vm != heuristics[heuristic][app][threads][vm]['selected']['instance']['name']:
                        data[heuristic]['change'] += 1
                    else:
                        data[heuristic]['nochange'] += 1

fig, ax = plt.subplots(figsize=(5, 2))
temp = np.array([])
gainloss = np.array([data[h]['change'] for h in article_heuristics])
ax.bar([heuristic_name[h] for h in article_heuristics], gainloss, 0.35, 
            label='Different as the current', color='#525150')
nochange = np.array([data[h]['nochange'] for h in article_heuristics])
ax.bar([heuristic_name[h] for h in article_heuristics], nochange, 0.35, 
            label='Same as the current', color='#b8b7b4', bottom=gainloss)
lgnd = plt.legend(bbox_to_anchor=(0.5, 1.3), loc='upper center', ncol=1, 
                    facecolor='white', frameon=True)
for i in lgnd.legendHandles:
    i._sizes = [50]
#lgnd.get_frame().set_linewidth(100)
plt.ylabel('Amount of experiments')
plt.yticks([0, 50, 100, 150, 200, 250])
plt.savefig(GRAPHS_DIR+'/'+'bar-nochange.svg', dpi=100, 
            bbox_inches='tight', format='svg', pad_inches = 0)
plt.show()
plt.clf()


data = {}
total = {}
for heuristic in article_heuristics:
    data[heuristic] = {'perf': 0, 'both': 0, 'nochange': 0, 'gain/loss': 0, 'cost': 0,
                        'perf_': {'cost_less': 0, 'cost_high': 0, 'cost_eq': 0},
                        'cost_': {'perf_less': 0, 'perf_high': 0, 'perf_eq': 0},
                        'perf_cost': {'perf_less': 0, 'perf_high': 0,
                                        'cost_less': 0, 'cost_high': 0}}
    total[heuristic] = 0
    for app in heuristics[heuristic]:
        for threads in heuristics[heuristic][app]:
            for vm in heuristics[heuristic][app][threads]:
                if heuristics[heuristic][app][threads][vm]['current']['experiment']:
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
                    total[heuristic] +=1

fig, ax = plt.subplots(figsize=(5, 2))
temp = np.array([])
cost = np.array([data[h]['cost'] for h in article_heuristics])
ax.bar([heuristic_name[h] for h in article_heuristics], cost, 0.35, label='Similar cost', color=colors[1])
both = np.array([data[h]['both'] for h in article_heuristics])
ax.bar([heuristic_name[h] for h in article_heuristics], both, 0.35, label='Similar cost and performance', color=colors[3], bottom=cost)
perf = np.array([data[h]['perf'] for h in article_heuristics])
ax.bar([heuristic_name[h] for h in article_heuristics], perf, 0.35, label='Similar performance', color=colors[4], bottom=cost+both)
gainloss = np.array([data[h]['gain/loss'] for h in article_heuristics])
ax.bar([heuristic_name[h] for h in article_heuristics], gainloss, 0.35, label='Different cost and performance', color=colors[2], bottom=perf+cost+both)
print(cost)
print(both)
print(perf)
print(gainloss)
print(total)

lgnd = plt.legend(bbox_to_anchor=(0.5, 1.3), loc='upper center', ncol=1, 
                    facecolor='white', frameon=True)
for i in lgnd.legendHandles:
    i._sizes = [50]
#lgnd.get_frame().set_linewidth(100)
plt.ylabel('Amount of experiments')
plt.yticks([0, 50, 100, 150, 200, 250])
plt.savefig(GRAPHS_DIR+'/'+'bar-change.svg', dpi=100, 
            bbox_inches='tight', format='svg', pad_inches = 0)
plt.show()
plt.clf()


#----------------------------------------------- price
FILE_CONS = 'results/exp.nocons.json'
FILE = 'results/exp.json'
with open(FILE, 'r') as fp:
    heuristics = json.load(fp)
with open(FILE_CONS, 'r') as fp:
    heuristics_cons = json.load(fp)

data = {}
for heuristic in article_heuristics:
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
for heuristic in article_heuristics:
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

lgnd = plt.legend(loc='upper right', ncol=1, facecolor='white', frameon=True)
for i in lgnd.legendHandles:
    i._sizes = [10]
plt.ylabel("Performance Speedup")
plt.xlabel("Cost Reduction")
plt.hlines(1, 0.7, 2.2, color='#000')
plt.vlines(1, 0.4, 1.5, color='#000')
plt.xlim(0.7, 2.2)
plt.ylim(0.4, 1.5)
#plt.xticks([0.70, 0.80, 0.90, 1.00, 1.10])
plt.savefig(GRAPHS_DIR+'/'+'conservatism-means.svg', dpi=100,
            bbox_inches='tight', format='svg', pad_inches = 0)
plt.show()
plt.clf()
