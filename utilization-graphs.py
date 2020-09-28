import matplotlib.pyplot as plt
import random
import numpy as np

random.seed(1)
DEMANDS_ORDER = {'high': 2, 'low': 1, 'idle': 0}
DEMANDS = {'high': [8000, 10000],
           'low': [1500, 7500],
           'idle': [0, 1000]}
RECOMENDATION = {'veryhigh': [9500, 10000]}
recomendations = {'veryhigh': []}

secondary_utilization = ['high']
dem = ['high', 'high', 'high']
high_long = {   'name': 'high-long',
                'cut': 5,
                'duration': 60*2,
                'utilization': [dem[1]] + [dem[0]]*2 + [dem[1]] + [dem[0]]*4 + [dem[2]] + [dem[0]]*5 + [dem[2]]
            }
high_medium = {  'name': 'high-medium',
                'cut': 5,
                'duration': 60*2,
                'utilization': [dem[1]] + [dem[0]]*2 + [dem[1]] + [dem[0]]*2 + [dem[2]] + [dem[0]]*2 + [dem[1]] + [dem[0]]
            }
freq_high_period_medium = [dem[0]] + [dem[1]] + [dem[0]]*2 + [dem[2]] + [dem[0]]*3 + [dem[1]] + [dem[0]]*2
freq_high_period_short = [dem[1]*5, dem[0], dem[1]*5]*10
freq_moderate = [dem[0]]*2 + [dem[1]] + [dem[2]] + [dem[2]] + [dem[1]] + [dem[2]] + [dem[0]]*2 + [dem[1]] + [dem[2]]


data = {'name': dem[0]+'2-'+secondary_utilization[0],
        'cut': 5,
        'duration': 60*24,
        'utilization': [dem[1]] + [dem[0]]*2 + [dem[1]] + [dem[0]]*4 + [dem[2]] + [dem[0]]*5 + [dem[2]]
        }
set_cut = True
cut = data['cut']
utilization = data['utilization']
duration = data['duration']
FILE_NAME = 'graphs/'+data['name']

random_utilization = False
rate_transition = 0.15
perturbation = int(duration/10)
price_instance1 = 0.50
price_instance2 = 1.00
price_instance3 = 2.00

cost1 = []
wastage1 = {'high': [], 'low': [], 'idle': [], 'total': []}
cost2 = []
wastage2 = {'high': [], 'low': [], 'idle': [], 'total': []}
cost3 = []
wastage3 = {'high': [], 'low': [], 'idle': [], 'total': []}

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

    for j in RECOMENDATION:
        if number >= RECOMENDATION[j][0]/100.0 and number <= RECOMENDATION[j][1]/100.0:
            recomendations[j].append(100)
        else:
            recomendations[j].append(0)


    cost1.append((cost1[-1] if len(cost1)>0 else 0) + price_instance1/60)
    wastage1[demand_list[i]].append((wastage1[demand_list[i]][-1] if len(wastage1[demand_list[i]])>0 else 0) +(100.00-number)/100.0*price_instance1/60)

    cost2.append((cost2[-1] if len(cost2)>0 else 0) + price_instance2/60)
    wastage2[demand_list[i]].append((wastage2[demand_list[i]][-1] if len(wastage2[demand_list[i]])>0 else 0) +(100.00-number)/100.0*price_instance2/60)
    
    cost3.append((cost3[-1] if len(cost3)>0 else 0) + price_instance3/60)
    wastage3[demand_list[i]].append((wastage3[demand_list[i]][-1] if len(wastage3[demand_list[i]])>0 else 0) +(100.00-number)/100.0*price_instance3/60)
    
    for j in ['high', 'low', 'idle']:
        if j != demand_list[i]:
            wastage1[j].append(wastage1[j][-1] if len(wastage1[j])>0 else 0)
            wastage2[j].append(wastage2[j][-1] if len(wastage2[j])>0 else 0)
            wastage3[j].append(wastage3[j][-1] if len(wastage3[j])>0 else 0)
    wastage1['total'].append(wastage1['high'][-1]+wastage1['low'][-1]+wastage1['idle'][-1])
    wastage2['total'].append(wastage2['high'][-1]+wastage2['low'][-1]+wastage2['idle'][-1])
    wastage3['total'].append(wastage3['high'][-1]+wastage3['low'][-1]+wastage3['idle'][-1])


secondary_demand_list = []
if random_utilization:
    for i in range(0, duration):
        secondary_demand_list.append(random.choice(secondary_utilization))
else:
    if not set_cut:
        cut = round(duration/len(secondary_utilization))
    d = -1
    for i in range(0, duration):
        if set_cut:
            if i%cut == 0:
                d+=1
            if d == len(secondary_utilization):
                d = 0
        elif i%cut == 0 and d+1<len(secondary_utilization):
            d+=1
        secondary_demand_list.append(secondary_utilization[d])
secondary_samples = []
for i in range(0, duration):
    if i == 0:
        if random.choice(['first', 'last']) == 'first':
            first = DEMANDS[secondary_demand_list[i]][0]
            last = DEMANDS[secondary_demand_list[i]][0] + (DEMANDS[secondary_demand_list[i]][1]-DEMANDS[secondary_demand_list[i]][0])*rate_transition
        else:
            first = DEMANDS[secondary_demand_list[i]][1] - (DEMANDS[secondary_demand_list[i]][1]-DEMANDS[secondary_demand_list[i]][0])*rate_transition
            last = DEMANDS[secondary_demand_list[i]][1]
    elif secondary_demand_list[i] != secondary_demand_list[i-1]:
        if DEMANDS_ORDER[secondary_demand_list[i]] > DEMANDS_ORDER[secondary_demand_list[i-1]]:
            first = DEMANDS[secondary_demand_list[i]][0]
            last = DEMANDS[secondary_demand_list[i]][0] + (DEMANDS[secondary_demand_list[i]][1]-DEMANDS[secondary_demand_list[i]][0])*rate_transition
        else:
            first = DEMANDS[secondary_demand_list[i]][1] - (DEMANDS[secondary_demand_list[i]][1]-DEMANDS[secondary_demand_list[i]][0])*rate_transition
            last = DEMANDS[secondary_demand_list[i]][1]
    else:
        transition = random.choice([1]*perturbation+[-1]*perturbation+[0])
        oldfirst = first
        if transition:
            first = first + transition*(last-oldfirst)*rate_transition
            last = last + transition*(last-oldfirst)*rate_transition
        else:
            if random.choice(['first', 'last']) == 'first':
                if random.choice(['restart', 'average']) == 'restart':
                    first = DEMANDS[secondary_demand_list[i]][0]
                    last = DEMANDS[secondary_demand_list[i]][0] + (DEMANDS[secondary_demand_list[i]][1] - DEMANDS[secondary_demand_list[i]][0])*rate_transition
                else:
                    first = DEMANDS[secondary_demand_list[i]][0] + (DEMANDS[secondary_demand_list[i]][1] - DEMANDS[secondary_demand_list[i]][0])*0.5
                    last = DEMANDS[secondary_demand_list[i]][1] - (DEMANDS[secondary_demand_list[i]][1]-first)*rate_transition
            else:
                if random.choice(['restart', 'average']) == 'restart':
                    first = DEMANDS[secondary_demand_list[i]][1] - (DEMANDS[secondary_demand_list[i]][1] - DEMANDS[secondary_demand_list[i]][0])*rate_transition
                    last = DEMANDS[secondary_demand_list[i]][1]
                else:
                    last = DEMANDS[secondary_demand_list[i]][0] + (DEMANDS[secondary_demand_list[i]][1] - DEMANDS[secondary_demand_list[i]][0])*0.5
                    first = DEMANDS[secondary_demand_list[i]][0] + (last - DEMANDS[secondary_demand_list[i]][0])*rate_transition
                    

    if last > DEMANDS[secondary_demand_list[i]][1]:
        last = DEMANDS[secondary_demand_list[i]][1]
    if first < DEMANDS[secondary_demand_list[i]][0]:
        first = DEMANDS[secondary_demand_list[i]][0]
    if int(first) == int(last):
        if random.choice(['first', 'last']) == 'first':
            first = DEMANDS[secondary_demand_list[i]][0]
            last = DEMANDS[secondary_demand_list[i]][0] + (DEMANDS[secondary_demand_list[i]][1]-DEMANDS[secondary_demand_list[i]][0])*rate_transition
        else:
            first = DEMANDS[secondary_demand_list[i]][1] - (DEMANDS[secondary_demand_list[i]][1]-DEMANDS[secondary_demand_list[i]][0])*rate_transition
            last = DEMANDS[secondary_demand_list[i]][1] 
    first = int(first)
    last = int(last) 
    number = random.randrange(first, last)/100.0
    secondary_samples.append(number)




fig = plt.figure()
ax = fig.add_subplot()
#ax.add_artist(plt.Rectangle((0, 0), duration, 10, facecolor='#ff977a', edgecolor='violet', linewidth=2.0))
#ax.add_artist(plt.Rectangle((0, 10), duration, 80, facecolor='#fffc96', edgecolor='violet', linewidth=2.0))
#ax.add_artist(plt.Rectangle((0, 80), duration, 100, facecolor='#99ff82', edgecolor='violet', linewidth=2.0))
ax.hlines(10, 0, duration, linestyles='dashed', color='#db1807')
ax.hlines(80, 0, duration, linestyles='dashed', color='#15ab07')
for j in RECOMENDATION:
    ax.bar(np.arange(duration), recomendations['veryhigh'], label='veryhigh', color='#a5faac')
plt.margins(0)
plt.ylim(0, 100)
plt.plot(samples, color='#f7aa2d', label='primary')
plt.plot(secondary_samples, color='#44b0fc', label='secondary')
plt.ylabel('utilization [%]')
plt.xlabel('time [min]')
plt.legend()
plt.yticks([0,10,50,80,100])
plt.xticks(samples_ticks)
plt.title('unidade: '+str(cut)+'min')
plt.savefig(FILE_NAME+'.png', dpi=60)
plt.show()

plt.hlines(1, 0, duration, linestyles=(0, (5, 10)), color='#ffd024')
plt.hlines(2, 0, duration, linestyles=(0, (5, 10)), color='#ff9c24')
plt.hlines(5, 0, duration, linestyles=(0, (5, 10)), color='#ff7824')
plt.hlines(10, 0, duration, linestyles=(0, (5, 10)), color='#ff4924')
plt.hlines(20, 0, duration, linestyles=(0, (5, 10)), color='#ff2424')
plt.plot(cost1, color='#ff2441', linestyle='dashdot', label='cost')
plt.plot(wastage1['high'], color='#f0b75b', linestyle='solid', label='high')
plt.plot(wastage1['low'], color='#ff4aae', linestyle='solid', label='low')
plt.plot(wastage1['idle'], color='#246dff', linestyle='solid', label='idle')
plt.plot(wastage1['total'], color='#5bf069', linestyle='solid', label='total')
plt.ylabel('price [USD]')
plt.xlabel('time [min]')
plt.legend()
plt.margins(0)
plt.yticks([0,1,2,5,10])
plt.xticks(samples_ticks)
plt.ylim(top=max(wastage1['high'][-1],wastage1['low'][-1],wastage1['idle'][-1])+1)
plt.title('Instance of price USD' + str(price_instance1) + ' cost '+"{:.2f}".format(cost1[-1]))
#plt.savefig(FILE_NAME+'-wastage1.png', dpi=60)
#plt.show()

plt.hlines(1, 0, duration, linestyles=(0, (5, 10)), color='#ffd024')
plt.hlines(2, 0, duration, linestyles=(0, (5, 10)), color='#ff9c24')
plt.hlines(5, 0, duration, linestyles=(0, (5, 10)), color='#ff7824')
plt.hlines(10, 0, duration, linestyles=(0, (5, 10)), color='#ff4924')
plt.hlines(20, 0, duration, linestyles=(0, (5, 10)), color='#ff2424')
plt.plot(cost2, color='#ff2441', linestyle='dashdot', label='cost')
plt.plot(wastage2['high'], color='#f0b75b', linestyle='solid', label='high')
plt.plot(wastage2['low'], color='#ff4aae', linestyle='solid', label='low')
plt.plot(wastage2['idle'], color='#246dff', linestyle='solid', label='idle')
plt.plot(wastage2['total'], color='#5bf069', linestyle='solid', label='total')
plt.ylabel('price [USD]')
plt.xlabel('time [min]')
plt.legend()
plt.margins(0)
plt.yticks([0,1,2,5,10])
plt.xticks(samples_ticks)
plt.ylim(top=max(wastage2['high'][-1],wastage2['low'][-1],wastage2['idle'][-1])+1)
plt.title('Instance of price USD' + str(price_instance2) + ' cost '+"{:.2f}".format(cost2[-1]))
#plt.savefig(FILE_NAME+'-wastage2.png', dpi=60)
#plt.show()
plt.clf()


plt.hlines(1, 0, duration, linestyles=(0, (5, 10)), color='#ffd024')
plt.hlines(2, 0, duration, linestyles=(0, (5, 10)), color='#ff9c24')
plt.hlines(5, 0, duration, linestyles=(0, (5, 10)), color='#ff7824')
plt.hlines(10, 0, duration, linestyles=(0, (5, 10)), color='#ff4924')
plt.hlines(20, 0, duration, linestyles=(0, (5, 10)), color='#ff2424')
plt.plot(cost3, color='#ff2441', linestyle='dashdot', label='cost')
plt.plot(wastage3['high'], color='#f0b75b', linestyle='solid', label='high')
plt.plot(wastage3['low'], color='#ff4aae', linestyle='solid', label='low')
plt.plot(wastage3['idle'], color='#246dff', linestyle='solid', label='idle')
plt.plot(wastage3['total'], color='#5bf069', linestyle='solid', label='total')
plt.ylabel('price [USD]')
plt.xlabel('time [min]')
plt.legend()
plt.margins(0)
plt.yticks([0,1,2,5,10])
plt.xticks(samples_ticks)
plt.ylim(top=max(wastage3['high'][-1],wastage3['low'][-1],wastage3['idle'][-1])+1)
plt.title('Instance of price USD' + str(price_instance3) + '|| cost USD'+"{:.2f}".format(cost3[-1]))
plt.savefig(FILE_NAME+'-wastage3.png', dpi=60)
plt.show()



