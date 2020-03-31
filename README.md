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
        */2 * * * * python /home/ubuntu/monitoring-system/audit-system.py
        */2 * * * * python /home/ubuntu/monitoring-system/control-system.py

Then:

    sudo systemctl restart cron.service
