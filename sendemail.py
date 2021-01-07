import smtplib
import os
from email.mime.text import MIMEText
home = os.path.dirname(os.path.realpath(__file__))

EMAIL_USER = (open(home+"/private/email_user", "r")).read().strip('\n')
EMAIL_PASSWORD = (open(home+"/private/email_password", "r")).read().strip('\n')
WEBSITE = (open(home+"/private/website", "r")).read().strip('\n')


def send_email(emails, subject, message):
    s = smtplib.SMTP_SSL(host='smtp.gmail.com', port=465)
    s.ehlo()
    s.login(EMAIL_USER, EMAIL_PASSWORD)
    msg = MIMEText(message)
    msg['Subject'] = subject
    msg['From'] = EMAIL_USER
    msg['To'] = emails
    #s.sendmail(EMAIL_USER, emails, msg.as_string())
    s.close()


def notregistered_email(emails, host):
    message = """WARNING: YOU HAVE AN INSTANCE THAT IS NOT BEING MONITORED!\n
    Please, install the agent in your instance (%s), more info you can find
     here: %s""" % (host, WEBSITE)
    subject = "URGENT: there is an unregistered host"
    if type(emails) is list:
        emails = ", ".join(emails)
    send_email(emails, subject, message)


def availablevolume_email(emails, volume):
    message = """WARNING: YOU HAVE A VOLUME THAT HAS NOT BEEN USED FOR A LONG TIME!\n
    Please, you need to verify if the volume %s can be deleted
    More info you can find here: %s""" % (volume, WEBSITE)
    subject = "URGENT: there is an unused volume"
    if type(emails) is list:
        emails = ", ".join(emails)
    send_email(emails, subject, message)


def userregistered_email(emails, user):
    message = """Hello!\n\n
    Now your hosts are going to be monitored by Zabbix.\n
    Username: %s\n
    You can get more info here: %s""" % (user, WEBSITE)
    subject = "Welcome to Zabbix monitoring tool"
    if type(emails) is list:
        emails = ", ".join(emails)
    send_email(emails, subject, message)


def usernotfound_email(emails, user):
    message = """There is an user not registered in Zabbix!\n
    Please, register this user: %s \n
    More info you can find here: %s""" % (user, WEBSITE)
    subject = "URGENT: there is an unregistered user"
    if type(emails) is list:
        emails = ", ".join(emails)
    send_email(emails, subject, message)


def quotaexceeded_email(emails, quota, wastage):
    message = """You do not have more money to waste!\n
    Your quota is USD %.2f and you have wasted USD %.2f\n
    You can ask more to admin.
    %s""" % (quota, round(wastage, 2), WEBSITE)
    subject = "URGENT: You do not have more money to waste!"
    if type(emails) is list:
        emails = ", ".join(emails)
    send_email(emails, subject, message)

def notificationaction_email(emails, instance, bucket, wastage, amount):
    message = """Your VM %s is wasting too much in this state %s\n
    This VM has wasted %.2f USD already\n
    This is the amount of time you recieved an notification in this state for this VM: %d.
    %s""" % (instance, bucket, round(wastage, 2), amount, WEBSITE)
    subject = "URGENT: You are wasting too much!"
    if type(emails) is list:
        emails = ", ".join(emails)
    send_email(emails, subject, message)


def recommendationaction_email(emails, instance, bucket, wastage, amount, recommendation):
    message = """Your VM %s is wasting too much in this state %s\n
    This VM has wasted %.2f USD already\n
    This is the amount of time you recieved an notification in this state for this VM: %d.
    %s""" % (instance, bucket, round(wastage, 2), amount, WEBSITE)
    message += recommendation
    subject = "URGENT: You are wasting too much!"
    if type(emails) is list:
        emails = ", ".join(emails)
    send_email(emails, subject, message)

def interventionaction_email(emails, instance, bucket, wastage, amount):
    message = """Your VM %s is wasting too much in this state %s\n
    This VM has wasted %.2f USD already\n
    This VM has been stopped.
    This is the amount of time you recieved an notification in this state for this VM: %d.
    %s""" % (instance, bucket, round(wastage, 2), amount, WEBSITE)
    subject = "URGENT: We stopped your instance! You are wasting too much!"
    if type(emails) is list:
        emails = ", ".join(emails)
    send_email(emails, subject, message)