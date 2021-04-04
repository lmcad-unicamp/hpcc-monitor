import os
import numpy as np
import scipy.stats

dir = os.path.dirname(os.path.realpath(__file__)) + '/'

monitoring_data = []
nomonitoring_data = []
for file in os.listdir(dir):
    if file.endswith(".nomonitoring.exp"):
        #print(int(os.popen("gawk '/ParamountItEnd/ {NUM+=1} END {print NUM}' "+dir+file).read().rstrip()))
        pi = float(os.popen("gawk '/ParamountItEnd/ {if (NUM<100) SUM+=$10; NUM+=1;} END {print SUM/100/1000/1000}' "+dir+file).read().rstrip())
        #pi = os.popen("gawk '/ParamountItEnd/ {SUM+=$10} END {print SUM/NR/1000/1000}' "+dir+'/'+file).read().rstrip()
        nomonitoring_data.append(float(pi))
    if file.endswith(".monitoring.exp"):
        #print(int(os.popen("gawk '/ParamountItEnd/ {NUM+=1} END {print NUM}' "+dir+file).read().rstrip()))
        pi = float(os.popen("gawk '/ParamountItEnd/ {if (NUM<100) SUM+=$10; NUM+=1;} END {print SUM/100/1000/1000}' "+dir+file).read().rstrip())
        #pi = os.popen("gawk '/ParamountItEnd/ {SUM+=$10} END {print SUM/NR/1000/1000}' "+dir+'/'+file).read().rstrip()
        monitoring_data.append(float(pi))
def mean_confidence_interval(data, confidence=0.95):
    a = 1.0 * np.array(data)
    n = len(a)
    m, se = np.mean(a), scipy.stats.sem(a)
    h = se * scipy.stats.t.ppf((1 + confidence) / 2., n-1)
    return h
print(nomonitoring_data)
print('no-monitoring-mean:', np.mean(nomonitoring_data))
print('no-monitoring-median:', np.median(nomonitoring_data))
print('no-monitoring-confidence:', mean_confidence_interval(nomonitoring_data))
print(monitoring_data)
print('monitoring-mean:', np.mean(monitoring_data))
print('monitoring-median:', np.median(monitoring_data))
print('monitoring-confidence:', mean_confidence_interval(monitoring_data))