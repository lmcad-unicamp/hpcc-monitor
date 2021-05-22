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
FILE = 'results/exp2.json'
with open(FILE, 'r') as fp:
    heuristics = json.load(fp)
GRAPHS_DIR = 'graphs'
if not os.path.exists(GRAPHS_DIR):
    os.makedirs(GRAPHS_DIR)


upper_right = {}
lower_right = {}
lower_left = {}
total = {}
for heuristic in price_heuristics:
    upper_right[heuristic] = 0
    lower_right[heuristic] = 0
    lower_left[heuristic] = 0
    total[heuristic] = 0
    for app in heuristics[heuristic]:
        for threads in heuristics[heuristic][app]:
            for vm in heuristics[heuristic][app][threads]:
                if heuristics[heuristic][app][threads][vm]['current']['experiment']:
                    if round(heuristics[heuristic][app][threads][vm]['ovcost'], 1) < 1.00:
                        lower_left[heuristic] +=1
                    if round(heuristics[heuristic][app][threads][vm]['ovperf'], 1) > 1.00:
                        upper_right[heuristic] +=1
                    if round(heuristics[heuristic][app][threads][vm]['ovcost'], 1) > 1.00 and\
                        round(heuristics[heuristic][app][threads][vm]['ovperf'], 1) < 1.00:
                        lower_right[heuristic] +=1
                    total[heuristic] +=1
print(lower_left)
print(upper_right)
print(lower_right)
print(total)

ind = np.arange(4)
width = 0.1
fig = plt.figure(figsize=(6.4, 2.5))
ax = fig.add_subplot(111)
lower_left_amount = np.array([lower_left[h]*100/total[h] for h in price_heuristics])
print(lower_left_amount)
rects1 = ax.bar(ind-width, lower_left_amount, width, color=colors[1])
lower_right_amount = np.array([lower_right[h]*100/total[h] for h in price_heuristics])
print(lower_right_amount)
rects2 = ax.bar(ind, lower_right_amount, width, color=colors[2])
upper_right_amount = np.array([upper_right[h]*100/total[h] for h in price_heuristics])
print(upper_right_amount)
rects3 = ax.bar(ind+width, upper_right_amount, width, color=colors[3])

ax.set_ylabel('Scores')
plt.ylabel('Percentage of experiments')
plt.ylim(0, 100)
plt.yticks([0, 10, 20, 30, 40, 60, 80, 100])
ax.set_xticks(ind + width / 2)
ax.set_xticklabels([heuristic_name[h] for h in price_heuristics])

ax.legend( (rects1[0], rects2[0], rects3[0]), ('Lower left', 'Lower right', 'Upper right'),
            loc='upper right', ncol=1, facecolor='white', frameon=True)
plt.savefig(GRAPHS_DIR+'/'+'bar-quadrants.svg', dpi=100, 
            bbox_inches='tight', format='svg', pad_inches=0)
plt.show()
plt.clf()


#----------------------------------------------- price-reason

upper_right = {}
upper_left = {}
lower_right = {}
lower_left = {}
total = {}
for heuristic in pricereason_heuristics:
    upper_right[heuristic] = 0
    upper_left[heuristic] = 0
    lower_right[heuristic] = 0
    lower_left[heuristic] = 0
    total[heuristic] = 0
    for app in heuristics[heuristic]:
        for threads in heuristics[heuristic][app]:
            for vm in heuristics[heuristic][app][threads]:
                if heuristics[heuristic][app][threads][vm]['current']['experiment']:
                    if round(heuristics[heuristic][app][threads][vm]['ovcost'], 1) < 1.00 and\
                        round(heuristics[heuristic][app][threads][vm]['ovperf'], 1) < 1.00:
                        lower_left[heuristic] +=1
                    if round(heuristics[heuristic][app][threads][vm]['ovcost'], 1) > 1.00 and\
                        round(heuristics[heuristic][app][threads][vm]['ovperf'], 1) > 1.00:
                        upper_right[heuristic] +=1
                    if round(heuristics[heuristic][app][threads][vm]['ovcost'], 1) < 1.00 and\
                        round(heuristics[heuristic][app][threads][vm]['ovperf'], 1) > 1.00:
                        upper_left[heuristic] +=1
                    if round(heuristics[heuristic][app][threads][vm]['ovcost'], 1) > 1.00 and\
                        round(heuristics[heuristic][app][threads][vm]['ovperf'], 1) < 1.00:
                        lower_right[heuristic] +=1
                    total[heuristic] +=1
print(lower_left)
print(upper_left)
print(upper_right)
print(lower_right)
print(total)

ind = np.arange(4)
width = 0.1
fig = plt.figure(figsize=(6.4, 2.5))
ax = fig.add_subplot(111)
lower_left_amount = np.array([lower_left[h]*100/total[h] for h in pricereason_heuristics])
print(lower_left_amount)
rects1 = ax.bar(ind-2*width, lower_left_amount, width, color=colors[1])
upper_left_amount = np.array([upper_left[h]*100/total[h] for h in pricereason_heuristics])
print(upper_left_amount)
rects2 = ax.bar(ind-width, upper_left_amount, width, color=colors[4])
lower_right_amount = np.array([lower_right[h]*100/total[h] for h in pricereason_heuristics])
print(lower_right_amount)
rects3 = ax.bar(ind, lower_right_amount, width, color=colors[2])
upper_right_amount = np.array([upper_right[h]*100/total[h] for h in pricereason_heuristics])
print(upper_right_amount)
rects4 = ax.bar(ind+width, upper_right_amount, width, color=colors[3])

ax.set_ylabel('Scores')
plt.ylabel('Percentage of experiments')
plt.ylim(0, 100)
plt.yticks([0, 10, 20, 40, 60, 80, 100])
ax.set_xticks(ind + width / 2)
ax.set_xticklabels([heuristic_name[h] for h in pricereason_heuristics])

ax.legend( (rects1[0], rects2[0], rects3[0], rects4[0]), ('Lower left', 'Upper left', 'Lower right', 'Upper right'),
            loc='upper right', ncol=1, facecolor='white', frameon=True)
plt.savefig(GRAPHS_DIR+'/'+'bar-quadrants-pr.svg', dpi=100, 
            bbox_inches='tight', format='svg', pad_inches=0)
plt.show()
plt.clf()

