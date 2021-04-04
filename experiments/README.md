This is the experiment scripts, results and graphs folder.

Folders:
```
blast-paramount-iteration: is a basic experiment using BLAST (not concluded)
installation-time: is the experiment to measure the installation time of Zabbix agent
limited-threads: is the experiment that limits the number of threads
monitoring-impact: is the experiment to measure the impact of monitoring in application's performance
unlimited-threads: is the experiment that does not limit the number of threads
```

Files:
```
experiments.py: gets the limited-threads and unlimited-threads results, calculates the performance and cost overheads based on the paramount iterations (see more below)
graphs-comparison.py: creates graphs for the comparison of heuristics
graphs-conservatism.py: creates graphs for the conservatism of heuristics
graphs-relation-to-application.py: creates graphs to the relation between heuristics and applications
graphs-relation-to-heuristics.py: creates graphs to the relation between the heuristics
graphs-relation-to-utilization.py: creates graphs to the relation between heuristics and vCPU utilization rate

results.tar.xz: see below

simulation-execution-demands.py: creates the graphs of a simulation of demands for execution finality
simulation-interactive-demands.py: creates the graphs of a simulation of demands for interactive finality
simulation-io-wastage.py: creates the graphs of a simulation an application with io stages
simulation-stopped-wastage.py: creates the graphs of a simulation an application that stops
simulation-stoppedio-wastage.py: creates the graphs of a simulation an application with io stages and that stops

table.py: creates the tables for LaTeX
```


## experiments.py

To execute:
changes the output filename here:
```
EXPERIMENTS_FILE = EXPERIMENTS_DIR + "/" + "exp2.40.json"
```


Comment the experiments you do not want to consider (limited or unlimited):
```
for i in APP:
    DIR[i] = {}
    #DIR[i]['experiment4'] = 'limited-threads/4/'+i+'/'
    #DIR[i]['experiment16'] = 'limited-threads/16/'+i+'/'
    DIR[i]['experiments'] = 'unlimited-threads/experiments/'+i+'/'
    DIR[i]['selections'] = 'unlimited-threads/selections/'+i+'/'
```

The input file of graphs and table scripts must use the JSON created by this program.

## results.tar.xz
```
results/exp.40.json: the results for limited and unlimited threads experiment
results/exp1.40.json: the results for limited threads experiment
results/exp2.40.json: the results for unlimited threads experiment
```