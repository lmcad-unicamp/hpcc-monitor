# Monitoring System

First install packages:

	sh installation.sh

Then, configure with:

	python3 configure.py

You can use cron to execute Audit and Control Systems periodically

	crontab -e

Write (with the right paths):

```
  * * * * * /usr/bin/python3 /home/ubuntu/monitoring-system/control-system.py >> /home/ubuntu/control-out.txt
  * * * * * /usr/bin/python3 /home/ubuntu/monitoring-system/audit-system.py >> /home/ubuntu/audit-out.txt
  * * * * * /usr/bin/python3 /home/ubuntu/monitoring-system/calculator.py >> /home/ubuntu/calculator-out.txt
```

Verify if it is active (if not, change 'status' to 'start'):

  sudo systemctl status cron.service

To get log of cron:

	grep CRON /var/log/syslog


## Configuration

### Audit-system

In the audit-system.py file you can define the time IN SECONDS for some notifications:
```
NOTREGISTERED_INSTANCES_TIME_TO_NOTIFY: time to notify about not registered instances
AVAILABLE_VOLUMES_FIRST_TIME_TO_NOTIFY: time to the first notification about available volumes
AVAILABLE_VOLUMES_TIME_TO_NOTIFY: time to the next notifications about available volumes
NOTREGISTERED_USERS_TIME_TO_NOTIFY: time to notify about not registered users
STARTING_INSTANCES_TIME_TO_NOTIFY: time since the instance's launch time to start audit it
```

### Calculator

You can configure the calculator in calculatorsetting.py

The calculator categorizes the VM in different buckets and uses a metric to quantify wastage.


```
bucket.py: is the categorization algorithm, you can define new demands in calculatorsetting.py, but new finalities need to be added to the code
selection.py: is the selection algorithm with different heuristics, you can define more heuristics by adding it in virtualmachine_selection function
equations.py: is the wastage quantification, you can define other equations, just alter the virtualmachine_calculates function
action.py: are the actions that the system can take, you can define new actions, just add they to the take_action function
```

### Zabbix configuration

You must define [autoregistration actions](https://www.zabbix.com/documentation/4.0/manual/discovery/auto_registration).

```
zabbix-export - has the templates defined for our Zabbix server
```

You can add another monitoring server, you must develop all functions presented in zapi.py and import the file.

### Providers

We only developed the  API for AWS, but you can add APIs for other cloud providers. 
You must develop all functions presented in aws.py using the respective provider API and add it to the audit-system and control-system.


## This repository


```
/experiments: the experiment scripts and results folder
actions.py: see Calculator section
audit-system.py: is the code for the Auditor component
aws.py: is the AWS API
buckets.py: see Calculator section
calculator.py: is the code for the Wastage Monitor component
calculatorsetting.py: see Calculator section
configure.py: is the script to configure the system
control-system.py: is the Controller component
create-user.py: is the script to execute to create a new user
equations.py: see Calculator section
installation.sh: is the system requirements installacion script
selections.py: see Calculator section
sendemail.py: the code to send emails
wastageapi.py: the class to deal with the wastage history of each VM
zabbix-agentd-install.sh: is the agent installation script to be executed in the VMs to be monitored
zabbix-configuration.sh: is the agent configuration script to be executed in the VMs to be monitored
zapi.py: is the Zabbix API
```
