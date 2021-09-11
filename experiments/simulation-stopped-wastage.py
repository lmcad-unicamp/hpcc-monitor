import matplotlib.pyplot as plt
import random
import numpy as np
import os
from pprint import pprint

random.seed(0)
DEMANDS_ORDER = {'very': 3, 'high': 2, 'low': 1, 'idle': 0}
DEMANDS = {'high': [8600, 10000],
           'low': [5000, 8400],
           'idle': [0, 1000]}
#DEMANDS = {'very': [7600, 10000],
#           'high': [5100, 7400],
#           'low': [1100, 4900],
#           'idle': [100, 900]}

#dem = ['very', 'high', 'low', 'idle']
dem = ['high', 'low', 'idle']

data = {'name': 'stopped-application',
        'cut': 5,
        'duration': 600,
        'utilization': [dem[0]]*108 + [dem[2]]*12
        #'utilization': [dem[1]] + [dem[0]] + [dem[0]] + [dem[0]]*2 + [dem[2]]*2 + [dem[1]]*2 + [dem[3]]
        #'utilization': [dem[1]] + [dem[0]]*2 + [dem[1]] + [dem[0]]*4 + [dem[2]] + [dem[0]]*5 + [dem[2]]
        }

set_cut = True
cut = data['cut']
utilization = data['utilization']
duration = data['duration']

GRAPHS_DIR = 'graphs-simulation'
if not os.path.exists(GRAPHS_DIR):
    os.makedirs(GRAPHS_DIR)
FILE_NAME = GRAPHS_DIR+'/'+data['name']

random_utilization = False
rate_transition = 0.15
perturbation = int(duration/10)


def get_price(utilization):
    #if utilization < 15.00:
    #    return 0.5
    if utilization < 25.00:
        return 1.5
    if utilization < 50.00:
        return 2.0
    if utilization < 75.00:
        return 2.5
    if utilization < 90.00:
        return 3.0
    if utilization <= 100.00:
        return 3.5
current_price = get_price(100.0)
    

cost = []
arbitrarywastage = {'very': [], 'high': [], 'low': [], 'idle': [], 'total': []}
wastagereset = {'very': [], 'high': [], 'low': [], 'idle': [], 'total': []}

demand_list = []
samples_ticks = []
if random_utilization:
    for i in range(0, duration):
        demand_list.append(random.choice(utilization))
else:
    if not set_cut:
        cut = round(duration/len(utilization))
    d = -1
    for i in range(0, duration):
        if set_cut:
            if i%cut == 0:
                d+=1
                if d == 0:
                    if utilization[0] != utilization[-1]:
                        samples_ticks.append(i)
                elif d != len(utilization):
                    if utilization[d] != utilization[d-1]:
                        samples_ticks.append(i)
                else:
                    if utilization[0] != utilization[d-1]:
                        samples_ticks.append(i)

            if d == len(utilization):
                d = 0
        elif i%cut == 0 and d+1<len(utilization):
            d+=1
            samples_ticks.append(i)
        demand_list.append(utilization[d])
samples_ticks.append(duration)


samples = []
for i in range(0, duration):
    if i == 0:
        if random.choice(['first', 'last']) == 'first':
            first = DEMANDS[demand_list[i]][0]
            last = DEMANDS[demand_list[i]][0] + (DEMANDS[demand_list[i]][1]-DEMANDS[demand_list[i]][0])*rate_transition
        else:
            first = DEMANDS[demand_list[i]][1] - (DEMANDS[demand_list[i]][1]-DEMANDS[demand_list[i]][0])*rate_transition
            last = DEMANDS[demand_list[i]][1]
    elif demand_list[i] != demand_list[i-1]:
        if DEMANDS_ORDER[demand_list[i]] > DEMANDS_ORDER[demand_list[i-1]]:
            first = DEMANDS[demand_list[i]][0]
            last = DEMANDS[demand_list[i]][0] + (DEMANDS[demand_list[i]][1]-DEMANDS[demand_list[i]][0])*rate_transition
        else:
            first = DEMANDS[demand_list[i]][1] - (DEMANDS[demand_list[i]][1]-DEMANDS[demand_list[i]][0])*rate_transition
            last = DEMANDS[demand_list[i]][1]
    else:
        transition = random.choice([1]*perturbation+[-1]*perturbation+[0])
        oldfirst = first
        if transition:
            first = first + transition*(last-oldfirst)*rate_transition
            last = last + transition*(last-oldfirst)*rate_transition
        else:
            if random.choice(['first', 'last']) == 'first':
                if random.choice(['restart', 'average']) == 'restart':
                    first = DEMANDS[demand_list[i]][0]
                    last = DEMANDS[demand_list[i]][0] + (DEMANDS[demand_list[i]][1] - DEMANDS[demand_list[i]][0])*rate_transition
                else:
                    first = DEMANDS[demand_list[i]][0] + (DEMANDS[demand_list[i]][1] - DEMANDS[demand_list[i]][0])*0.5
                    last = DEMANDS[demand_list[i]][1] - (DEMANDS[demand_list[i]][1]-first)*rate_transition
            else:
                if random.choice(['restart', 'average']) == 'restart':
                    first = DEMANDS[demand_list[i]][1] - (DEMANDS[demand_list[i]][1] - DEMANDS[demand_list[i]][0])*rate_transition
                    last = DEMANDS[demand_list[i]][1]
                else:
                    last = DEMANDS[demand_list[i]][0] + (DEMANDS[demand_list[i]][1] - DEMANDS[demand_list[i]][0])*0.5
                    first = DEMANDS[demand_list[i]][0] + (last - DEMANDS[demand_list[i]][0])*rate_transition
                    

    if last > DEMANDS[demand_list[i]][1]:
        last = DEMANDS[demand_list[i]][1]
    if first < DEMANDS[demand_list[i]][0]:
        first = DEMANDS[demand_list[i]][0]
    if int(first) == int(last):
        if random.choice(['first', 'last']) == 'first':
            first = DEMANDS[demand_list[i]][0]
            last = DEMANDS[demand_list[i]][0] + (DEMANDS[demand_list[i]][1]-DEMANDS[demand_list[i]][0])*rate_transition
        else:
            first = DEMANDS[demand_list[i]][1] - (DEMANDS[demand_list[i]][1]-DEMANDS[demand_list[i]][0])*rate_transition
            last = DEMANDS[demand_list[i]][1] 
    first = int(first)
    last = int(last) 
    number = random.randrange(first, last)/100.0
    samples.append(number)

    price_selected = get_price(number)
    cost.append((cost[-1] if len(cost)>0 else 0) + current_price/60)
    arbitrarywastage[demand_list[i]].append((arbitrarywastage[demand_list[i]][-1] if len(arbitrarywastage[demand_list[i]])>0 else 0) + (current_price-price_selected)/60)
    wastagereset[demand_list[i]].append((wastagereset[demand_list[i]][-1] if len(wastagereset[demand_list[i]])>0 else 0) +(current_price-price_selected)/60)
    

    for j in ['very', 'high', 'low', 'idle']:
        if j != demand_list[i]:
            arbitrarywastage[j].append(arbitrarywastage[j][-1] if len(arbitrarywastage[j])>0 else 0)
            wastagereset[j].append(0)
    arbitrarywastage['total'].append(arbitrarywastage['very'][-1]+arbitrarywastage['high'][-1]+arbitrarywastage['low'][-1]+arbitrarywastage['idle'][-1])





fig = plt.figure()
ax = fig.add_subplot()
#ax.add_artist(plt.Rectangle((0, 0), duration, 10, facecolor='#ff977a', edgecolor='violet', linewidth=2.0))
#ax.add_artist(plt.Rectangle((0, 10), duration, 80, facecolor='#fffc96', edgecolor='violet', linewidth=2.0))
#ax.add_artist(plt.Rectangle((0, 80), duration, 100, facecolor='#99ff82', edgecolor='violet', linewidth=2.0))
ax.hlines(10, 0, duration, linestyles='dashed', color='#db1807')
ax.hlines(85, 0, duration, linestyles='dashed', color='#15ab07')
ax.hlines(25, 0, duration, linestyles='dotted', color='#246dff')
ax.hlines(50, 0, duration, linestyles='dotted', color='#246dff')
ax.hlines(75, 0, duration, linestyles='dotted', color='#246dff')
ax.hlines(90, 0, duration, linestyles='dotted', color='#246dff')
plt.margins(0)
plt.ylim(0, 100)
plt.plot(samples, color='#f7aa2d', label='primary')
plt.ylabel('vCPU utilization [%]')
plt.xlabel('time [min]')
#plt.legend()
plt.yticks([0,10,25,50,75,85,90,100])
plt.xticks(samples_ticks)
plt.savefig(FILE_NAME+'-utilization.svg', dpi=100,
            bbox_inches='tight', format='svg', pad_inches = 0)
plt.show()

plt.hlines(1, 0, duration, linestyles=(0, (5, 10)), color='#ffd024')
plt.hlines(2, 0, duration, linestyles=(0, (5, 10)), color='#ff9c24')
plt.hlines(5, 0, duration, linestyles=(0, (5, 10)), color='#ff7824')
plt.hlines(10, 0, duration, linestyles=(0, (5, 10)), color='#ff4924')
plt.hlines(20, 0, duration, linestyles=(0, (5, 10)), color='#ff2424')
plt.plot(cost, color='#ff2441', linestyle='dashdot', label='cost')
#plt.plot(arbitrarywastage['very'], color='#118185', linestyle='solid', label='>75%')
plt.plot(arbitrarywastage['high'], color='#f0b75b', linestyle='solid', label='high')
plt.plot(arbitrarywastage['low'], color='#ff4aae', linestyle='solid', label='low')
plt.plot(arbitrarywastage['idle'], color='#246dff', linestyle='solid', label='idle')
#plt.plot(wastagereset['idle'], color='red', linestyle='dashed', label='idle-reset')
plt.plot(arbitrarywastage['total'], color='#5bf069', linestyle='solid', label='total')
plt.ylabel('USD')
plt.xlabel('time [min]')
plt.legend(ncol=3,loc='center', bbox_to_anchor=(0.5,1.05))
plt.margins(0)
plt.yticks([0,1,2,5,10])
plt.xticks(samples_ticks)
plt.ylim(top=max(arbitrarywastage['high'][-1],arbitrarywastage['low'][-1],arbitrarywastage['idle'][-1])+1)
plt.savefig(FILE_NAME+'-wastage.svg', dpi=100,
            bbox_inches='tight', format='svg', pad_inches = 0)
plt.show()

plt.hlines(1, 0, duration, linestyles=(0, (5, 10)), color='#ffd024')
plt.hlines(2, 0, duration, linestyles=(0, (5, 10)), color='#ff9c24')
plt.hlines(5, 0, duration, linestyles=(0, (5, 10)), color='#ff7824')
plt.hlines(10, 0, duration, linestyles=(0, (5, 10)), color='#ff4924')
plt.hlines(20, 0, duration, linestyles=(0, (5, 10)), color='#ff2424')
plt.plot(cost, color='#ff2441', linestyle='dashdot', label='cost')
#plt.plot(arbitrarywastage['very'], color='#118185', linestyle='solid', label='>75%')
plt.plot(arbitrarywastage['high'], color='#f0b75b', linestyle='solid', label='high')
plt.plot(arbitrarywastage['low'], color='#ff4aae', linestyle='solid', label='low')
plt.plot(arbitrarywastage['idle'], color='#246dff', linestyle='solid', label='idle')
plt.plot(wastagereset['idle'], color='#7303fc', linestyle='dashed', label='idle-reset')
plt.plot(arbitrarywastage['total'], color='#5bf069', linestyle='solid', label='total')
plt.ylabel('USD')
plt.xlabel('time [min]')
plt.legend(ncol=3,loc='center', bbox_to_anchor=(0.5,1.05))
plt.margins(0)
plt.yticks([0,1,2,5,10])
plt.xticks(samples_ticks)
plt.ylim(top=max(arbitrarywastage['high'][-1],arbitrarywastage['low'][-1],arbitrarywastage['idle'][-1])+1)
plt.savefig(FILE_NAME+'-wastage-reset.svg', dpi=100,
            bbox_inches='tight', format='svg', pad_inches = 0)
plt.show()