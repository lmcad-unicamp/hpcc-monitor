from experiments import scipy, json, os, re, heuristic_name, article_heuristics, sortedbyvcpu, INSTANCES 
from pprint import pprint

FILE = 'results/exp1.article.json'
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

data = {}


for h in article_heuristics:
    if h not in data: data[h] = {}
    for app in heuristics[h]:
        for t in heuristics[h][app]:
            for vm in heuristics[h][app][t]:
                if heuristics[h][app][t][vm]['current']['experiment']:
                    print(heuristics[h][app][t][vm]['current']['instance']['name'])
        break
    break

for h in article_heuristics:
    if h not in data: data[h] = {}
    for app in heuristics[h]:
        for t in heuristics[h][app]:
            for vm in heuristics[h][app][t]:
                if heuristics[h][app][t][vm]['current']['experiment']:
                    print(heuristics[h][app][t][vm]['current']['cost'])
        break
    break

for h in article_heuristics:
    if h not in data: data[h] = {}
    for app in heuristics[h]:
        for t in heuristics[h][app]:
            for vm in heuristics[h][app][t]:
                if heuristics[h][app][t][vm]['current']['experiment']:
                    print(heuristics[h][app][t][vm]['current']['pi'])
        break
    break

for h in article_heuristics:
    print(h)
    if h not in data: data[h] = {}
    for app in heuristics[h]:
        print(app)
        for t in heuristics[h][app]:
            #t = '16'
            for vm in heuristics[h][app][t]:
                if heuristics[h][app][t][vm]['current']['experiment']:
                    if heuristics[h][app][t][vm]['blocal-cost'] == heuristics[h][app][t][vm]['selected']['instance']['name']:
                        print("SIM")
                    else:
                        print("NAO")
        break