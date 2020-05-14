import logging
import os
import inspect
import json
import MySQLdb
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
    def __init__(self, HISTORY_ITEMS_FILE):
        self.HISTORY_ITEMS_FILE = HISTORY_ITEMS_FILE
        self.history_wastage = {}
        # Get history of wastage from file
        if os.path.isfile(HISTORY_ITEMS_FILE):
            try:
                self.history_wastage = json.loads((open(HISTORY_ITEMS_FILE,
                                                        'r')).read())
            except json.decoder.JSONDecodeError:
                pass

        pprint(self.history_wastage)

        # Get user wastage and quota from database
        self.users = {}
        cursor.execute("SELECT * FROM User_Wastage")
        for user in list(cursor.fetchall()):
            self.users[user[0]] = {}
            self.users[user[0]]['quota'] = float(user[1])
            self.users[user[0]]['total'] = float(user[2])
            self.users[user[0]]['permonth'] = float(user[3])
            if user[4] == CURRENT_MONTH:
                self.users[user[0]]['month'] = user[4]
            else:
                self.users[user[0]]['month'] = 0

    def __del__(self):
        # Update file
        (open(self.HISTORY_ITEMS_FILE,
              "w")).write(json.dumps(self.history_wastage))

        # Update database
        for user in self.users:
            cursor.execute("UPDATE User_Wastage SET WastageTotal="
                           + str(self.users[user]['total'])
                           + ",WastageLastMonth="
                           + str(self.users[user]['permonth'])
                           + ",Month="+str(self.users[user]['month'])
                           + " WHERE UserName=\'" + user
                           + "\'")
            #con.commit()

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

    # Delete host from history
    def delete_host(self, host):
        del self.history_wastage[host]
        logger.info("[WASTAGEAPI] [delete_host] Host deleted " + host)

    # Add new host to history
    def add_host(self, host):
        self.history_wastage[host] = {}
        self.history_wastage[host]['wastage'] = 0
        self.history_wastage[host]['prices'] = {}
        self.history_wastage[host]['prices']['timestamps'] = []
        self.history_wastage[host]['prices']['values'] = []
        logger.info("[WASTAGEAPI] [add_host] Host added " + host)

    # Get history of a host
    def get_host_history(self, host):
        return self.history_wastage[host]

    # Set wastage of a host
    def set_host_wastage(self, host, heuristic, wastage):
        self.history_wastage[host][heuristic]['wastage'] = wastage

    # Get wastage of a host
    def get_host_wastage(self, host, heuristic):
        return self.history_wastage[host][heuristic]['wastage']

    # Set a heuristic for host if it exists:
    def set_heuristic(self, host, heuristic):
        if heuristic not in self.history_wastage[host]:
            self.history_wastage[host][heuristic] = {}
            self.history_wastage[host][heuristic]['wastage'] = 0.0


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

    # Get history of an item
    def get_item_history(self, host, HEURISTIC, item):
        if item in self.history_wastage[host][HEURISTIC]:
            return self.history_wastage[host][HEURISTIC][item]
        else:
            return {}

    # Set history to an item
    def set_item_history(self, host, HEURISTIC, item, history):
        self.history_wastage[host][HEURISTIC][item] = history
