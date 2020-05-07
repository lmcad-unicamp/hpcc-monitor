# Monitoring System

First install packages:

	sh installation.sh

Then, configure with:

	python configure.py

You can use cron to execute Audit and Control Systems periodically

	crontab -e

Write (with the right paths):

	* * * * * /usr/bin/python3 /home/ubuntu/monitoring-system/audit-system.py >> /home/ubuntu/audit-out.txt
	* * * * * /usr/bin/python3 /home/ubuntu/monitoring-system/control-system.py >> /home/ubuntu/control-out.txt

Verify if it is active (if not, change 'status' to 'start'):

  sudo systemctl status cron.service

To get log of cron:

	grep CRON /var/log/syslog
