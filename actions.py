import logging
import os
import inspect
import calculatorsetting as cs
import zapi as monitorserver
import awsapi as aws
from datetime import datetime
from pprint import pprint
from sendemail import notificationaction_email, recommendationaction_email, interventionaction_email

TIME_BETWEEN_ACTIONS = cs.ACTION_TIME_BETWEEN_ACTIONS
AMOUNT_OF_ACTIONS_TAKEN = cs.ACTION_AMOUNT_OF_ACTIONS_TAKEN

THRESHOLDS = {'execution': {'high': {'accumulative': {
                                        'thresholds': [3], 
                                        'action': ['notification']}},
                            'low': {'accumulative': {
                                        'thresholds': [2], 
                                        'action': ['recommendation']}},
                            'idle': {'accumulative': {
                                        'thresholds': [2], 
                                        'action': ['notification']}, 
                                     'reset': {
                                        'thresholds': [1], 
                                        'action': ['intervention']}}},
            'server':      {'high': {'accumulative': {
                                        'thresholds': [3], 
                                        'action': ['notification']},
                                    'reset': {
                                        'thresholds': [1], 
                                        'action': ['recommendation']}},
                            'low': {'accumulative': {
                                        'thresholds': [3], 
                                        'action': ['recommendation']}},
                            'idle': {'accumulative': {
                                        'thresholds': [3], 
                                        'action': ['recommendation']}}},
            'interaction': {'high': {'accumulative': {
                                        'thresholds': [3], 
                                        'action': ['notification']},
                                     'reset': {
                                        'thresholds': [1], 
                                        'action': ['recommendation']}},
                            'low': {'accumulative': {
                                        'thresholds': [3], 
                                        'action': ['recommendation']}},
                            'idle': {'accumulative': {
                                        'thresholds': [3], 
                                        'action': ['recommendation']}}},
            }

home = os.path.dirname(os.path.realpath(__file__))
logger = logging.getLogger(str(inspect.getouterframes(inspect.currentframe()
                                                      )[-1].filename))

def intervention(host):
    if host['provider'] == 'aws':
        aws.stop_instance(host['id'])


def take_action(host, bucket, selection, wastage, amount, action):
    try:
        emails = monitorserver.get_user_email(host['user'])
        if amount >= AMOUNT_OF_ACTIONS_TAKEN:
            emails.append(monitorserver.get_admins_email())
    except monitorserver.NotFoudException:
        emails = monitorserver.get_admins_email()
    if action == 'notification':
        if cs.MODE == 'monitoring':
            notificationaction_email(emails, host['id'], bucket, wastage, amount)
    elif action == 'recommendation':
        if bucket == 'execution-low' or bucket == 'interaction-low' or bucket == 'server-low':
            recommendation = """\nYou should choose a cheaper instance type.\n
            Maybe one with the exact vCPU amount you are using.\n
            I have selected this instance type for you: %s\n""" % (selection)
        if bucket == 'server-high' or bucket == 'interaction-high':
            recommendation = """\nYou should choose a better instance type.\n
            Maybe one with more vCPU amount, because you are highly using it."""
        if bucket == 'server-idle' or bucket == 'interaction-idle':
            recommendation = """\nYou should choose a cheaper instance type.\n
            Maybe one with the exact vCPU amount you are using.\n
            I have selected this instance type for you: %s\n""" % (selection)
        if cs.MODE == 'monitoring':
            recommendationaction_email(emails, host['id'], bucket, wastage, amount, recommendation)
    elif action == 'intervention':
        intervention(host)
        if cs.MODE == 'monitoring':
            interventionaction_email(emails, host['id'], bucket, wastage, amount)

    logger.info("[ACTIONS] An action was taken for instance " + host['id'])

def virtualmachine_action(host, virtualmachines, timestamp, bucket, selection):
    finality = bucket.split('-')[0]
    demand = bucket.split('-')[1]
    
    wastages = virtualmachines.get_bucket(host['id'], bucket)

    threshold = None
    takeaction = False
    for t in range(len(THRESHOLDS[finality][demand]['accumulative']['thresholds'])):
        threshold = (THRESHOLDS[finality][demand]['accumulative']['thresholds'][t]
                        *virtualmachines.find_price(host['id'], timestamp))
        if threshold <= wastages['arbitrary']:
            threshold = t
            takeaction = True
        else: break

    actions_infos = virtualmachines.get_bucket_action(host['id'], bucket)
    if takeaction and cs.NOW - actions_infos['timestamp'] >= TIME_BETWEEN_ACTIONS:
        actions_infos['timestamp'] = cs.NOW
        actions_infos['amount'] += 1
        virtualmachines.set_bucket_action(host['id'], bucket, actions_infos)
        take_action(host, bucket, selection, wastages['arbitrary'], actions_infos['amount'],
                    THRESHOLDS[finality][demand]['accumulative']['action'][t])


    
    if 'reset' in THRESHOLDS[finality][demand]:
        threshold = None
        takeaction = False
        for t in range(len(THRESHOLDS[finality][demand]['reset']['thresholds'])):
            threshold = (THRESHOLDS[finality][demand]['reset']['thresholds'][t]
                        *virtualmachines.find_price(host['id'], timestamp))
            if t <= wastages['reset']:
                threshold = t
                takeaction = True
            else: break

        actions_infos = virtualmachines.get_bucket_action(host['id'], bucket, 'reset_action')
        if takeaction and cs.NOW - actions_infos['timestamp'] >= TIME_BETWEEN_ACTIONS:
            actions_infos['timestamp'] = cs.NOW
            actions_infos['amount'] += 1
            virtualmachines.set_bucket_action(host['id'], bucket, actions_infos, 'reset_action')
            take_action(host, bucket, selection, wastages['reset'], actions_infos['amount'],
                        THRESHOLDS[finality][demand]['accumulative']['action'][t])

