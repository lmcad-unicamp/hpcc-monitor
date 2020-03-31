import pyzabbix
import sys
from getpricing import getpricing

hostid = sys.argv[1]
hostname = sys.argv[2]

macros = zapi.host.get(hostids=hostid, selectMacros="extend", output=["macros"])
hostprice = getpricing(hostname)
macros = []
flag = False
flagprice = False
for macro in macrosFromHost[0]['macros']:
    if '{$PRICE}' in macro['macro']:
        flag = True
        flagprice = True
        value = macro['value']
        if float(value) != float(hostprice):
            flagprice = False
            macro['value'] = hostprice
            print("[PRICING] PRICE OF "+str(hostname)+" UPDATED FROM "+str(value)+" TO "+str(hostprice))
    macros.append(macro)

if not flag:
    macro = {'macro':'{$PRICE}', 'value':str(hostprice)}
    macros.append(macro)
    print("[PRICING] PRICE OF "+str(hostname)+" ADDED COSTING "+str(hostprice))

if not flagprice:
    try:
        zapi.host.update(hostid=hostid, macros=macros)
    except NotFoudException as e:
        print(e)
