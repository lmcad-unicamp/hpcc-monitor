"""
Authors: William Felipe C. Tavares, Marcio Roberto Miranda Assis, Edson Borin
Copyright Unicamp
"""
import logging
import os
import inspect
import json
import MySQLdb
import atexit
from datetime import datetime, timezone
from pprint import pprint

home = os.path.dirname(os.path.realpath(__file__))
logger = logging.getLogger(str(inspect.getouterframes(inspect.currentframe()
                                                      )[-1].filename))
DBSERVER = (open(home+"/private/db_server", "r")).read().strip('\n')
DBUSER = (open(home+"/private/db_user", "r")).read().strip('\n')
DBPASSWORD = (open(home+"/private/db_password", "r")).read().strip('\n')

# Get acces to database
con = MySQLdb.connect(DBSERVER, DBUSER, DBPASSWORD)
con.select_db('db_quota_manager')
cursor = con.cursor()

CURRENT_MONTH = int(datetime.utcnow().replace(tzinfo=timezone.utc).month)


class HistoryWastage:
    def __init__(self, HISTORY_FILE, mode):
        self.mode = mode
        if self.mode == 'monitoring':
            self.HISTORY_FILE = HISTORY_FILE
        elif self.mode == 'testing':
            self.HISTORY_FILE = HISTORY_FILE+'.test.json'
        elif self.mode == 'experimenting':
            self.HISTORY_FILE = ''

        self.history_wastage = {}
        # Get history of wastage from file
        if self.mode != 'experimenting' and os.path.isfile(self.HISTORY_FILE):
            try:
                self.history_wastage = json.loads((open(self.HISTORY_FILE,
                                                        'r')).read())
            except json.decoder.JSONDecodeError:
                pass
        self.update_hosts()
        atexit.register(self.finalization)
        # Get user wastage and quota from database
        self.users = {}
        cursor.execute("SELECT * FROM User_Wastage")
        for user in list(cursor.fetchall()):
            self.users[user[0]] = {}
            self.users[user[0]]['quota'] = float(user[1])
            self.users[user[0]]['total'] = float(user[2])
            if user[4] == CURRENT_MONTH:
                self.users[user[0]]['month'] = user[4]
                self.users[user[0]]['permonth'] = float(user[3])
            else:
                self.users[user[0]]['month'] = CURRENT_MONTH
                self.users[user[0]]['permonth'] = 0.0
        if self.mode == 'testing':
            pprint(self.history_wastage)
            # pprint(self.users)
            pprint("____________________________________________")

    def finalization(self):
        if self.mode == 'testing':
            pprint("____________________________________________")
            pprint(self.history_wastage)
            # pprint(self.users)
        if self.mode == 'experimenting':
            pprint("____________________________________________")
            # pprint(self.history_wastage)
        # Update file
        if self.mode != 'experimenting':
            (open(self.HISTORY_FILE, 'w+')).write(json.dumps(self.history_wastage))

        # Update database
        if self.mode == 'monitoring':
            for user in self.users:
                cursor.execute("UPDATE User_Wastage SET WastageTotal="
                               + str(self.users[user]['total'])
                               + ",WastageLastMonth="
                               + str(self.users[user]['permonth'])
                               + ",Month="+str(self.users[user]['month'])
                               + " WHERE UserName=\'" + user
                               + "\'")
                con.commit()

    # Get history of wastage
    def get_history(self):
        return self.history_wastage

    # Get hosts of history
    def get_hosts(self):
        return [host for host in self.history_wastage]

    # Get users
    def get_users(self):
        return self.users

    # Add wastage to the user, per month and total
    def add_user_wastage(self, user, wastage, wastage_timestamp):
        current_wastage_month = self.users[user]['permonth']
        current_wastage = self.users[user]['total']
        if (int(datetime.fromtimestamp(wastage_timestamp).month)
                == CURRENT_MONTH):
            self.users[user]['permonth'] = current_wastage_month + wastage
        self.users[user]['total'] = current_wastage + wastage

    # Get an attribute from a user
    def get_user_attribute(self, user, attribute):
        return self.users[user][attribute]

    # Add new attribute to a host
    def add_host_attribute(self, host, attribute, value):
        self.history_wastage[host][attribute] = value

    # Delete host from history
    def delete_host(self, host):
        del self.history_wastage[host]
        logger.info("[WASTAGEAPI] [delete_host] Host deleted " + host)

    # Add new host to history
    def add_host(self, host):
        self.history_wastage[host] = {}
        self.history_wastage[host]['last_time'] = 0
        self.history_wastage[host]['boot'] = 0
        self.history_wastage[host]['cost'] = 0
        self.history_wastage[host]['buckets'] = {}
        self.history_wastage[host]['buckets']['last_bucket'] = ''
        self.history_wastage[host]['buckets']['timestamp'] = 0
        self.history_wastage[host]['finalities'] = {}
        self.history_wastage[host]['finalities']['last_time'] = 0
        self.history_wastage[host]['finalities']['timestamps'] = []
        self.history_wastage[host]['finalities']['values'] = []
        self.history_wastage[host]['demands'] = {}
        self.history_wastage[host]['demands']['last_time'] = 0
        self.history_wastage[host]['demands']['timestamps'] = []
        self.history_wastage[host]['demands']['values'] = []
        self.history_wastage[host]['statistics'] = {}
        self.history_wastage[host]['prices'] = {}
        self.history_wastage[host]['prices']['timestamps'] = []
        self.history_wastage[host]['prices']['values'] = []
        self.history_wastage[host]['types'] = {}
        self.history_wastage[host]['types']['timestamps'] = []
        self.history_wastage[host]['types']['values'] = []
        logger.info("[WASTAGEAPI] [add_host] Host added " + host)

    # Update to the a new version
    def update_hosts(self):
        for host in self.history_wastage:
            if 'buckets' not in self.history_wastage[host]:
                self.history_wastage[host]['buckets'] = {}
                self.history_wastage[host]['buckets']['last_bucket'] = ''
                self.history_wastage[host]['buckets']['timestamp'] = 0

            if 'finalities' not in self.history_wastage[host]:
                self.history_wastage[host]['finalities'] = {}
                self.history_wastage[host]['finalities']['timestamps'] = []
                self.history_wastage[host]['finalities']['values'] = []

            if 'demands' not in self.history_wastage[host]:
                self.history_wastage[host]['demands'] = {}
                self.history_wastage[host]['demands']['timestamps'] = []
                self.history_wastage[host]['demands']['values'] = []
                
            if 'prices' not in self.history_wastage[host]:
                self.history_wastage[host]['prices'] = {}
                self.history_wastage[host]['prices']['timestamps'] = []
                self.history_wastage[host]['prices']['values'] = []

            if 'types' not in self.history_wastage[host]:
                self.history_wastage[host]['types'] = {}
                self.history_wastage[host]['types']['timestamps'] = []
                self.history_wastage[host]['types']['values'] = []

            if 'statistics' not in self.history_wastage[host]:
                self.history_wastage[host]['statistics'] = {}

            if 'boot' not in self.history_wastage[host]:
                self.history_wastage[host]['boot'] = 0

            if 'cost' not in self.history_wastage[host]:
                self.history_wastage[host]['cost'] = {}

    # Reste the reset values
    def reset_bucket(self, host, bucket):
        self.history_wastage[host]['buckets'][bucket]['reset_action']['amount'] = 0
        self.history_wastage[host]['buckets'][bucket]['reset_action']['timestamp'] = 0


    # Conver timelapse to string
    def timelapse_str(self, timelapse):
        return str(timelapse[0])+'-'+str(timelapse[1])

    # Get history of a host
    def get_host_history(self, host):
        return self.history_wastage[host]

    # Set wastage of a host
    def set_host_wastage(self, host, equation, wastage, timelapse=None):
        if timelapse:
            timelapse = self.timelapse_str(timelapse)
            self.history_wastage[host][timelapse][
                                                equation]['wastage'] = wastage
        else:
            self.history_wastage[host][equation]['wastage'] = wastage

    # Get wastage of a host
    def get_host_wastage(self, host, equation, timelapse=None):
        if timelapse:
            timelapse = self.timelapse_str(timelapse)
            return self.history_wastage[host][timelapse][equation]['wastage']
        else:
            return self.history_wastage[host][equation]['wastage']

    # Set cost of a host
    def set_host_cost(self, host, cost, timelapse=None):
        if timelapse:
            timelapse = self.timelapse_str(timelapse)
            self.history_wastage[host][timelapse]['cost'] = cost
        else:
            self.history_wastage[host]['cost'] = cost

    # Get cost of a host
    def get_host_cost(self, host, timelapse=None):
        if timelapse:
            timelapse = self.timelapse_str(timelapse)
            return self.history_wastage[host][timelapse]['cost']
        else:
            return self.history_wastage[host]['cost']

    # Set timestamp of the last time calculated
    def set_last_time(self, host, timestamp):
        self.history_wastage[host]['last_time'] = timestamp

    # Get timestamp of the last time calculated
    def get_last_time(self, host):
        return self.history_wastage[host]['last_time']

    # Set boot wastage of a host
    def set_host_boot(self, host, boot, timelapse=None):
        if timelapse:
            timelapse = self.timelapse_str(timelapse)
            self.history_wastage[host][timelapse]['boot'] = boot
        else:
            self.history_wastage[host]['boot'] = boot

    # Get boot wastage of a host
    def get_host_boot(self, host, timelapse=None):
        if timelapse:
            timelapse = self.timelapse_str(timelapse)
            return self.history_wastage[host][timelapse]['boot']
        else:
            return self.history_wastage[host]['boot']

    # Set statistics of a host
    def set_host_statistics(self, host, statistics, timelapse=None):
        if timelapse:
            timelapse = self.timelapse_str(timelapse)
            self.history_wastage[host][timelapse]['statistics'] = statistics
        else:
            self.history_wastage[host]['statistics'] = statistics

    # Get statistics of a host
    def get_host_statistics(self, host, timelapse=None):
        if timelapse:
            timelapse = self.timelapse_str(timelapse)
            return self.history_wastage[host][timelapse]['statistics']
        else:
            return self.history_wastage[host]['statistics']

    # Get timestamp of boot wastage of a host
    def get_host_boottimestamp(self, host):
        return self.history_wastage[host]['boottimestamp']

    # Set an attribute on equation
    def set_equation_attribute(self, host, equation, attribute, value):
        self.history_wastage[host][equation][attribute] = value

    # Set a equation for host if it exists:
    def set_equation(self, host, equation, timelapse=None):
        if timelapse:
            timelapse = self.timelapse_str(timelapse)
            if equation not in self.history_wastage[host][timelapse]:
                self.history_wastage[host][timelapse][equation] = {}
                self.history_wastage[host][timelapse][
                                                    equation]['wastage'] = 0.0
        else:
            if equation not in self.history_wastage[host]:
                self.history_wastage[host][equation] = {}
                self.history_wastage[host][equation]['wastage'] = 0.0

    # Get equation's attributes
    def get_equation(self, host, equation, timelapse=None):
        if timelapse:
            timelapse = self.timelapse_str(timelapse)
            if equation in self.history_wastage[host][timelapse]:
                return self.history_wastage[host][timelapse][equation]
            return {}
        else:
            if equation in self.history_wastage[host]:
                return self.history_wastage[host][equation]
            return {}

    # Get the last timestamp of price of host
    def get_price_timestamp(self, host):
        if self.history_wastage[host]['prices']['timestamps']:
            return self.history_wastage[host]['prices']['timestamps'][-1]
        else:
            return 0

    # Check if ther is any price history on host
    def has_price(self, host):
        if len(self.history_wastage[host]['prices']['values']) > 0:
            return True
        return False

    # Get price of the host in a specific timestamp
    def find_price(self, host, timestamp):
        prices = self.history_wastage[host]['prices']
        for i in reversed(range(len(prices['timestamps']))):
            if prices['timestamps'][i] <= timestamp:
                return float(prices['values'][i])
        return prices['values'][0]

    # Get prices between two timestamps
    def find_prices(self, host, begin, end):
        prices = self.history_wastage[host]['prices']
        period_prices = []
        for i in reversed(range(len(prices['timestamps']))):
            if prices['timestamps'][i] <= end:
                if prices['timestamps'][i] > begin:
                    period_prices.append([float(prices['values'][i]),
                                          prices['timestamps'][i]])
                else:
                    period_prices.append([float(prices['values'][i]),
                                          prices['timestamps'][i]])
                    break
        if len(period_prices) == 0:
            period_prices = [[float(prices['values'][0]), begin]]
        else:
            period_prices.reverse()
            period_prices[0][1] = begin
        return period_prices

    # Set the history of price of host
    def set_pricing_history(self, host, values):
        new_timestamps = []
        new_values = []
        for v in values:
            new_timestamps.append(int(v['timestamp']))
            new_values.append(float(v['value']))
        self.history_wastage[host]['prices']['timestamps'].extend(
                                                                new_timestamps)
        self.history_wastage[host]['prices']['values'].extend(new_values)

    # Get the last timestamp of type of host
    def get_type_timestamp(self, host):
        if self.history_wastage[host]['types']['timestamps']:
            return self.history_wastage[host]['types']['timestamps'][-1]
        else:
            return 0

    # Check if ther is any type history on host
    def has_type(self, host):
        if len(self.history_wastage[host]['types']['values']) > 0:
            return True
        return False

    # Get type of the host in a specific timestamp
    def find_type(self, host, timestamp):
        types = self.history_wastage[host]['types']
        for i in reversed(range(len(types['timestamps']))):
            if types['timestamps'][i] <= timestamp:
                return types['values'][i]
        return types['values'][0]

    # Get types between two timestamps
    def find_types(self, host, begin, end):
        types = self.history_wastage[host]['types']
        period_types = []
        for i in reversed(range(len(types['timestamps']))):
            if types['timestamps'][i] <= int(end):
                if types['timestamps'][i] > int(begin):
                    period_types.append([types['values'][i],
                                        types['timestamps'][i]])
                else:
                    period_types.append([types['values'][i],
                                        types['timestamps'][i]])
                    break
        if len(period_types) == 0:
            period_types = [[types['values'][0], int(begin)]]
        else:
            period_types.reverse()
            period_types[0][1] = int(begin)
        return period_types

    # Set the history of type of host
    def set_type_history(self, host, values):
        new_timestamps = []
        new_values = []
        for v in values:
            new_timestamps.append(int(v['timestamp']))
            new_values.append(v['value'])
        self.history_wastage[host]['types']['timestamps'].extend(
                                                                new_timestamps)
        self.history_wastage[host]['types']['values'].extend(new_values)

    # Get history of an item
    def get_item_history(self, host, item, timelapse=None):
        if timelapse:
            timelapse = self.timelapse_str(timelapse)
            if item in self.history_wastage[host][timelapse]:
                return self.history_wastage[host][timelapse][item]
            else:
                return {}
        else:
            if item in self.history_wastage[host]:
                return self.history_wastage[host][item]
            else:
                return {}

    # Set history to an item
    def set_item_history(self, host, item, history, timelapse=None):
        if timelapse:
            timelapse = self.timelapse_str(timelapse)
            self.history_wastage[host][timelapse][item] = history
        else:
            self.history_wastage[host][item] = history

    # Set a timelapse for host if it exists:
    def add_timelapse(self, host, timelapse):
        timelapsestr = self.timelapse_str(timelapse)
        if timelapsestr not in self.history_wastage[host]:
            self.history_wastage[host][timelapsestr] = {}
            self.history_wastage[host][timelapsestr]['cost'] = {}
            self.history_wastage[host][timelapsestr]['boot'] = {}
            self.history_wastage[host][timelapsestr]['bucket'] = {}
            self.history_wastage[host][timelapsestr]['time'] = (timelapse[1] -
                                                                timelapse[0])
            self.history_wastage[host][timelapsestr]['statistics'] = {}
            self.history_wastage[host][timelapsestr]['type'] = self.find_types(
                                    host, timelapse[0], timelapse[1])
            self.history_wastage[host][timelapsestr]['price'] = self.find_prices(
                                    host, timelapse[0], timelapse[1])

    # Set a bucket for host if it exists:
    def set_bucket(self, host, bucket, timelapse=None):
        if timelapse:
            timelapse = self.timelapse_str(timelapse)
            if bucket not in self.history_wastage[host][timelapse]['buckets']:
                self.history_wastage[host][timelapse]['buckets'][bucket] = {}
                self.history_wastage[host][timelapse]['buckets'][bucket][
                                                    'residual'] = 0.0
                self.history_wastage[host][timelapse]['buckets'][bucket][
                                                    'compulsory'] = 0.0
                self.history_wastage[host][timelapse]['buckets'][bucket][
                                                    'arbitrary'] = 0.0
                self.history_wastage[host][timelapse]['buckets'][bucket][
                                                    'reset'] = 0.0
                self.history_wastage[host][timelapse]['buckets'][bucket]['action'] = {}
                self.history_wastage[host][timelapse]['buckets'][bucket]['action'][
                                                    'timestamp'] = 0.0
                self.history_wastage[host][timelapse]['buckets'][bucket]['action'][
                                                    'amount'] = 0.0
        else:
            if bucket not in self.history_wastage[host]['buckets']:
                self.history_wastage[host]['buckets'][bucket] = {}
                self.history_wastage[host]['buckets'][bucket]['residual'] = 0.0
                self.history_wastage[host]['buckets'][bucket]['compulsory'] = 0.0
                self.history_wastage[host]['buckets'][bucket]['arbitrary'] = 0.0
                self.history_wastage[host]['buckets'][bucket]['reset'] = 0.0
                self.history_wastage[host]['buckets'][bucket]['action'] = {}
                self.history_wastage[host]['buckets'][bucket]['action']['timestamp'] = 0
                self.history_wastage[host]['buckets'][bucket]['action']['amount'] = 0
                self.history_wastage[host]['buckets'][bucket]['reset_action'] = {}
                self.history_wastage[host]['buckets'][bucket]['reset_action']['timestamp'] = 0
                self.history_wastage[host]['buckets'][bucket]['reset_action']['amount'] = 0

    # Get bucket's attributes
    def get_bucket(self, host, bucket, timelapse=None):
        if timelapse:
            timelapse = self.timelapse_str(timelapse)
            if bucket in self.history_wastage[host][timelapse]['buckets']:
                return self.history_wastage[host][timelapse]['buckets'][bucket]
            return {}
        else:
            if bucket in self.history_wastage[host]['buckets']:
                return self.history_wastage[host]['buckets'][bucket]
            return {}

    # Get buckets history
    def get_buckets(self, host, timelapse=None):
        if timelapse:
            timelapse = self.timelapse_str(timelapse)
            return self.history_wastage[host][timelapse]['buckets']
        else:
            return self.history_wastage[host]['buckets']

    # Get the last timestamp of bucket of host
    def get_bucket_timestamp(self, host):
        if self.history_wastage[host]['buckets']['timestamp']:
            return self.history_wastage[host]['buckets']['timestamp']
        else:
            return 0
    
    # Get the last value of bucket of host
    def get_bucket_value(self, host):
        if self.history_wastage[host]['buckets']['last_bucket']:
            return self.history_wastage[host]['buckets']['last_bucket']
        else:
            return 'none'

    # Update the last value of bucket of host
    def update_bucket_infos(self, host, last_bucket, timestamp):
        if timestamp > self.history_wastage[host]['buckets']['timestamp']:
            self.history_wastage[host]['buckets']['timestamp'] = timestamp
            self.history_wastage[host]['buckets']['last_bucket'] = last_bucket
    
    # Set an wastage on bucket
    def set_bucket_wastage(self, host, bucket, wastage, value):
        self.history_wastage[host]['buckets'][bucket][wastage] = value


    # Get the action infos of a bucket
    def get_bucket_action(self, host, bucket, action='action'):
        return self.history_wastage[host]['buckets'][bucket][action]

    # Set the action infos of a bucket
    def set_bucket_action(self, host, bucket, action_infos, action='action'):
        self.history_wastage[host]['buckets'][bucket][action] = action_infos


    # Get finality history
    def get_finality_history(self, host, timelapse=None):
        if timelapse:
            timelapse = self.timelapse_str(timelapse)
            return self.history_wastage[host][timelapse]['finalities']
        else:
            return self.history_wastage[host]['finalities']

    # Get the last timestamp of finality of host
    def get_finality_timestamp(self, host):
        if self.history_wastage[host]['finalities']['timestamps']:
            return self.history_wastage[host]['finalities']['timestamps'][-1]
        else:
            return 0
    
    
    # Set the last timestamp of finality of host
    def set_finality_last_time(self, host, timestamp):
        self.history_wastage[host]['finalities']['last_time'] = timestamp

    # Get the last timestamp of finality of host
    def get_finality_last_time(self, host):
        return self.history_wastage[host]['finalities']['last_time']

    # Get the last value of finality of host
    def get_finality_value(self, host):
        if self.history_wastage[host]['finalities']['values']:
            return self.history_wastage[host]['finalities']['values'][-1]
        else:
            return 'none'

    # Check if ther is any finality history on host
    def has_finality(self, host):
        if len(self.history_wastage[host]['finalities']['values']) > 0:
            return True
        return False

    # Get finality of the host in a specific timestamp
    def find_finality(self, host, timestamp):
        finalities = self.history_wastage[host]['finalities']
        for i in reversed(range(len(finalities['timestamps']))):
            if finalities['timestamps'][i] <= timestamp:
                return finalities['values'][i]
        return finalities['values'][0]

    # Get finalities between two timestamps
    def find_finalities(self, host, begin, end):
        finalities = self.history_wastage[host]['finalities']
        period_finalities = []
        for i in reversed(range(len(finalities['timestamps']))):
            if finalities['timestamps'][i] <= end:
                if finalities['timestamps'][i] > begin:
                    period_finalities.append([finalities['values'][i],
                                          finalities['timestamps'][i]])
                else:
                    period_finalities.append([finalities['values'][i],
                                          finalities['timestamps'][i]])
                    break
        if len(period_finalities) == 0:
            period_finalities = [[finalities['values'][0], begin]]
        else:
            period_finalities.reverse()
            period_finalities[0][1] = begin
        return period_finalities

    # Set the history of finality of host
    def set_finality_history(self, host, values, timestamp):
        new_timestamps = []
        new_values = []
        for v in values:
            new_timestamps.append(int(v['timestamp']))
            new_values.append(v['value'])
        self.set_finality_last_time(host, int(timestamp))
        self.history_wastage[host]['finalities']['timestamps'].extend(
                                                                new_timestamps)
        self.history_wastage[host]['finalities']['values'].extend(new_values)


    # Get demand history
    def get_demand_history(self, host, timelapse=None):
        if timelapse:
            timelapse = self.timelapse_str(timelapse)
            return self.history_wastage[host][timelapse]['demands']
        else:
            return self.history_wastage[host]['demands']

    # Get the last timestamp of demand of host
    def get_demand_timestamp(self, host):
        if self.history_wastage[host]['demands']['timestamps']:
            return self.history_wastage[host]['demands']['timestamps'][-1]
        else:
            return 0
    
    # Get the last timestamp of demand of host
    def get_demand_last_time(self, host):
        return self.history_wastage[host]['demands']['last_time']

    # Set the last timestamp of demand of host
    def set_demand_last_time(self, host, timestamp):
        self.history_wastage[host]['demands']['last_time'] = timestamp

    # Get the last value of demand of host
    def get_demand_value(self, host):
        if self.history_wastage[host]['demands']['values']:
            return self.history_wastage[host]['demands']['values'][-1]
        else:
            return 'none'

    # Check if ther is any demand history on host
    def has_demand(self, host):
        if len(self.history_wastage[host]['demands']['values']) > 0:
            return True
        return False

    # Get demand of the host in a specific timestamp
    def find_demand(self, host, timestamp):
        demands = self.history_wastage[host]['demands']
        for i in reversed(range(len(demands['timestamps']))):
            if demands['timestamps'][i] <= timestamp:
                return demands['values'][i]
        return demands['values'][0]

    # Get demands between two timestamps
    def find_demands(self, host, begin, end):
        demands = self.history_wastage[host]['demands']
        period_demands = []
        for i in reversed(range(len(demands['timestamps']))):
            if demands['timestamps'][i] <= end:
                if demands['timestamps'][i] > begin:
                    period_demands.append([demands['values'][i],
                                          demands['timestamps'][i]])
                else:
                    period_demands.append([demands['values'][i],
                                          demands['timestamps'][i]])
                    break
        if len(period_demands) == 0:
            period_demands = [[demands['values'][0], begin]]
        else:
            period_demands.reverse()
            period_demands[0][1] = begin
        return period_demands

    # Set the history of demand of host
    def set_demand_history(self, host, values, timestamp):
        new_timestamps = []
        new_values = []
        for v in values:
            new_timestamps.append(int(v['timestamp']))
            new_values.append(v['value'])
        self.set_demand_last_time(host, int(timestamp))
        self.history_wastage[host]['demands']['timestamps'].extend(
                                                                new_timestamps)
        self.history_wastage[host]['demands']['values'].extend(new_values)