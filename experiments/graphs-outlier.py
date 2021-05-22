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

FILE = 'results/exp2.json'
with open(FILE, 'r') as fp:
    heuristics = json.load(fp)
GRAPHS_DIR = 'graphs'
if not os.path.exists(GRAPHS_DIR):
    os.makedirs(GRAPHS_DIR)
#pprint(heuristics['vcpu']['EP'])
intel = ['c5n9xlarge', 'r512xlarge', 'c512xlarge', 'r5n12xlarge', 'i32xlarge',
        'r5xlarge', 'r52xlarge', 't32xlarge', 'r5n8xlarge', 'r58xlarge',
        'c5n4xlarge', 'i34xlarge', 'c54xlarge', 'r54xlarge', 'c59xlarge']
amd = ['r5a2xlarge', 'c5a8xlarge', 'r5axlarge', 'r5a8xlarge', 'c5a4xlarge']
intel_amd = {'ovcost': [], 'ovperf': []}
intel_intel = {'ovcost': [], 'ovperf': []}
amd_intel = {'ovcost': [], 'ovperf': []}
amd_amd = {'ovcost': [], 'ovperf': []}
for h in price_heuristics:
    for app in heuristics[h]:
        for t in heuristics[h][app]:
            for vm in heuristics[h][app][t]:
                if heuristics[h][app][t][vm]['current']['experiment']:
                    if vm != heuristics[h][app][t][vm]['selected']['instance']['name']:
                        vms = heuristics[h][app][t][vm]['selected']['instance']['name']
                        if vm in intel:
                            if vms in amd:
                                intel_amd['ovcost'].append([heuristics[h][app][t][vm]['ovcost']])
                                intel_amd['ovperf'].append([heuristics[h][app][t][vm]['ovperf']])
                            elif vms in intel:
                                intel_intel['ovcost'].append([heuristics[h][app][t][vm]['ovcost']])
                                intel_intel['ovperf'].append([heuristics[h][app][t][vm]['ovperf']])
                        elif vm in amd:
                            if vms in intel:
                                amd_intel['ovcost'].append([heuristics[h][app][t][vm]['ovcost']])
                                amd_intel['ovperf'].append([heuristics[h][app][t][vm]['ovperf']])
                            elif vms in amd:
                                amd_amd['ovcost'].append([heuristics[h][app][t][vm]['ovcost']])
                                amd_amd['ovperf'].append([heuristics[h][app][t][vm]['ovperf']])
colors = {'r5a8xlarge': '#FF0000',
          'c59xlarge': '#0000FF',
          'c5a4xlarge': '#FF6600',
          'c512xlarge': '#0cc202',
          'r5axlarge': '#c4a400',
          't32xlarge': '#e30079',
          'r54xlarge': '#7704c9',
          'r512xlarge': '#000000'}

plt.figure(figsize=(6.4, 3.5))
plt.scatter(intel_intel['ovcost'], intel_intel['ovperf'], c='#3e96ed', marker='D', 
            linewidth=0.7, alpha=1, s=7, label='Intel to Intel')
plt.scatter(intel_amd['ovcost'], intel_amd['ovperf'], c='#ed493e', marker='D', 
            linewidth=0.7, alpha=1, s=7, label='Intel to AMD')
plt.scatter(amd_amd['ovcost'], amd_amd['ovperf'], c='#500b78', marker='*', 
            linewidth=1, alpha=1, s=17, label='AMD to AMD')
plt.scatter(amd_intel['ovcost'], amd_intel['ovperf'], c='#0e8030', marker='*', 
            linewidth=1, alpha=1, s=17, label='AMD to Intel')

lgnd = plt.legend(loc='upper left', facecolor='white', frameon=True)
for i in lgnd.legendHandles:
    i._sizes = [50]
plt.ylabel("Performance Speedup")
plt.xlabel("Cost Reduction")
plt.hlines(1, 0.2, 3, color='#000')
plt.vlines(1, 0.25, 1.75, color='#000')
plt.xlim(0.2, 3)
plt.ylim(0.25, 1.75)
#plt.yticks([0.25, 0.50, 0.75, 1, 1.25, 1.5, 1.75, 2])
plt.savefig(GRAPHS_DIR+'/'+'outliers.svg', dpi=100,
            bbox_inches='tight', format='svg', pad_inches = 0)
plt.show()
plt.clf()


