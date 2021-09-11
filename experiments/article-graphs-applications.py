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


# --------------------- Experiment 1 - price-
FILE = 'results/exp1.json'
with open(FILE, 'r') as fp:
    heuristics = json.load(fp)
GRAPHS_DIR = 'graphs-article'
if not os.path.exists(GRAPHS_DIR):
    os.makedirs(GRAPHS_DIR)

data = {}
for h in article_heuristics:
    if h not in data: data[h] = {}
    for app in heuristics[h]:
        for t in heuristics[h][app]:
            for vm in heuristics[h][app][t]:
                if heuristics[h][app][t][vm]['current']['experiment']:
                    if vm != heuristics[h][app][t][vm]['selected']['instance']['name']:
                        app_name = (app.split('-'))[0]
                        app_thread = app_name + '-' + str(t)
                        if app_thread not in data[h]:
                            data[h][app_thread] = {}
                            data[h][app_thread] = {'app': app_name, 'threads': t, 
                                                    'cost': [], 'perf': []}
                            if app_thread == 'FT-16': data[h][app_thread]['app'] = 'FT-16'
                            if app_thread == 'FT-4': data[h][app_thread]['app'] = 'FT-4'
                        data[h][app_thread]['cost'].append(
                                                heuristics[h][app][t][vm]['ovcost'])
                        data[h][app_thread]['perf'].append(
                                                heuristics[h][app][t][vm]['ovperf'])


markers_heuristics=["*","D",'P','s']
alpha_heuristics=[1, 1, 1, 1]
sizes_heuristics=[60, 40, 50, 40]
ft4 = {}
fig = plt.figure(figsize=(6.4, 4))
for h in (data.copy()):
    if h not in ft4: ft4[h] = {}
    for a in data[h].copy():
        if a == "FT-4":
            if a not in ft4[h]: ft4[h][a] = {}
            ft4[h][a] = data[h][a]
            del data[h][a]

for h,m,al,s in zip(data, markers_heuristics, alpha_heuristics, sizes_heuristics):
    for a,c in zip(data[h], colors):
        plt.scatter(scipy.stats.mstats.gmean(data[h][a]['cost']),
                scipy.stats.mstats.gmean(data[h][a]['perf']),
                c=c, alpha=al, s=s, marker=m)

for h,m,al,s in zip(ft4, markers_heuristics, alpha_heuristics, sizes_heuristics):
    for a in ft4[h]:
        plt.scatter(scipy.stats.mstats.gmean(ft4[h][a]['cost']),
                scipy.stats.mstats.gmean(ft4[h][a]['perf']),
                c=colors[7], alpha=al, s=s, marker=m)

labels = []
for a in data[list(data.keys())[0]]:
    labels.append(data[list(data.keys())[0]][a]['app'])
for a in ft4[list(ft4.keys())[0]]:
    labels.append(ft4[list(ft4.keys())[0]][a]['app'])

handles = [f("8", colors[i]) for i in range(len(labels))]
lgnd = plt.legend(handles=handles, labels=labels, bbox_to_anchor=(0., 1.02, 1., .102), ncol=4)
ax = plt.gca().add_artist(lgnd)

handles = [f(markers_heuristics[i], "k") for i in range(4)]
labels = [heuristic_name[h] for h in article_heuristics]
plt.legend(handles=handles, labels=labels, loc='lower right', facecolor='white', frameon=True)

for i in lgnd.legendHandles:
    i._sizes = [10]
plt.ylabel("Performance Speedup")
plt.xlabel("Cost Reduction")
plt.hlines(1, 0.99, 4.5, color='#000')
plt.vlines(1, 0.3, 1.2, color='#000')
plt.xlim(0.99, 4.3)
plt.ylim(0.3, 1.2)
#plt.xticks([1.5, 2.0, 2.5, 3.0, 3.5, 4.0])
plt.savefig(GRAPHS_DIR+'/'+'exp1-application.svg', dpi=100, 
            bbox_inches='tight', format='svg', pad_inches = 0)
plt.show()
plt.clf()





# --------------------- Experiment 2 - price-

FILE = 'results/exp2.json'
with open(FILE, 'r') as fp:
    heuristics = json.load(fp)

data = {}
for h in article_heuristics:
    if h not in data: data[h] = {}
    for app in heuristics[h]:
        for t in heuristics[h][app]:
            for vm in heuristics[h][app][t]:
                if heuristics[h][app][t][vm]['current']['experiment']:
                    if vm != heuristics[h][app][t][vm]['selected']['instance']['name']:
                        app_name = (app.split('-'))[0]
                        app_thread = app_name
                        if app_thread not in data[h]:
                            data[h][app_thread] = {}
                            data[h][app_thread] = {'app': app_name, 'threads': t, 
                                                    'cost': [], 'perf': []}
                        data[h][app_thread]['cost'].append(
                                                heuristics[h][app][t][vm]['ovcost'])
                        data[h][app_thread]['perf'].append(
                                                heuristics[h][app][t][vm]['ovperf'])

markers_heuristics=["*","D",'P','s']
alpha_heuristics=[1, 0.5, 1, 1]
sizes_heuristics=[60, 40, 50, 40]
for h,m,al,s in zip(data, markers_heuristics, alpha_heuristics, sizes_heuristics):
    for a,c in zip(data[h], colors):
        plt.scatter(scipy.stats.mstats.gmean(data[h][a]['cost']),
                scipy.stats.mstats.gmean(data[h][a]['perf']),
               c=c, alpha=al, s=s, marker=m)
        #plt.errorbar(scipy.stats.mstats.gmean(data[h][a]['cost']), 
        #            scipy.stats.mstats.gmean(data[h][a]['perf']),
        #            yerr=mean_confidence_interval(data[h][a]['perf']),
        #            xerr=mean_confidence_interval(data[h][a]['cost']), 
        #           c=c, alpha=al, marker=m)


f = lambda m,c: plt.plot([],[],marker=m, color=c, ls="none")[0]

labels = []
for a in data[list(data.keys())[0]]:
    labels.append(data[list(data.keys())[0]][a]['app'])
handles = [f("8", colors[i]) for i in range(len(labels))]
lgnd = plt.legend(handles=handles, labels=labels, bbox_to_anchor=(0., 1.02, 1., .102), ncol=4)
ax = plt.gca().add_artist(lgnd)

handles = [f(markers_heuristics[i], "k") for i in range(4)]
labels = [heuristic_name[h] for h in article_heuristics]
plt.legend(handles=handles, labels=labels, loc='upper left', facecolor='white', frameon=True)

for i in lgnd.legendHandles:
    i._sizes = [10]
plt.ylabel("Performance Speedup")
plt.xlabel("Cost Reduction")
plt.hlines(1, 0.9, 1.7, color='#000')
plt.vlines(1, 0.6, 1.7, color='#000')
plt.xlim(0.9, 1.7)
plt.ylim(0.6, 1.7)
#plt.xticks([1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7])
plt.savefig(GRAPHS_DIR+'/'+'exp2-application.svg', dpi=100,
            bbox_inches='tight', format='svg', pad_inches = 0)
plt.show()
plt.clf()
