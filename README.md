# Monitoring System

First install packages:

	sh installation.sh

Then, configure with:

	python configure.py

You can use cron to execute Audit and Control Systems periodically

	crontab -e

Write:

	SHELL=/bin/bash
	PATH=/sbin:/bin:/usr/sbin:/usr/bin
	MAILTO=root
	HOME=/
	* * * * * python /home/ubuntu/monitoring-system/audit-system.py
	* * * * * python /home/ubuntu/monitoring-system/control-system.py

Then:

  sudo systemctl restart cron.service

To get log of cron:

	grep CRON /var/log/syslog
