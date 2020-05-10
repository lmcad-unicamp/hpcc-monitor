import smtplib
import os
from email.mime.text import MIMEText
home = os.path.dirname(os.path.realpath(__file__))

EMAIL_USER = (open(home+"/private/email_user", "r")).read().strip('\n')
EMAIL_PASSWORD = (open(home+"/private/email_password", "r")).read().strip('\n')


def notregistered_email(emails, host):
    s = smtplib.SMTP_SSL(host='smtp.gmail.com', port=465)
    s.ehlo()
    s.login(EMAIL_USER, EMAIL_PASSWORD)
    message = "WARNING: YOU HAVE AN INSTANCE THAT IS NOT BEING MONITORED!\n\n"
    message = message + "Please, install the agent in your instance (" + host + ")"
    message = message + ", more info you can find here: lmcad.com/zabbix"
    msg = MIMEText(message)
    msg['Subject'] = "URGENT: there is a host unregistered"
    msg['From'] = EMAIL_USER
    if type(emails) is list:
        msg['To'] = ", ".join(emails)
    else:
        msg['To'] = emails
    s.sendmail(EMAIL_USER, emails, msg.as_string())
    s.close()


def availablevolume_email(emails, volume):
    s = smtplib.SMTP_SSL(host='smtp.gmail.com', port=465)
    s.ehlo()
    s.login(EMAIL_USER, EMAIL_PASSWORD)
    message = "WARNING: YOU HAVE A VOLUME THAT HAS NOT BEEN USED FOR A LONG TIME!\n\n"
    message = message + "Please, you need to verify if the volume (" + volume + ") can be deleted"
    message = message + ", more info you can find here: lmcad.com/zabbix"
    msg = MIMEText(message)
    msg['Subject'] = "URGENT: there is an unused volume"
    msg['From'] = EMAIL_USER
    if type(emails) is list:
        msg['To'] = ", ".join(emails)
    else:
        msg['To'] = emails
    s.sendmail(EMAIL_USER, emails, msg.as_string())
    s.close()


def user_registered(email, username):
    s = smtplib.SMTP_SSL(host='smtp.gmail.com', port=465)
    s.ehlo()
    s.login(EMAIL_USER, EMAIL_PASSWORD)
    message = "Hello!\n\n"
    message = message + "Now your hosts are going to be monitored by Zabbix.\n"
    message = message + "Username: " + str(username) + "\n"
    message = message + "You can get more info here: lmcad.com/zabbix"
    msg = MIMEText(message)
    msg['Subject'] = "Welcome to Zabbix monitoring tool"
    msg['From'] = EMAIL_USER
    if type(email) is list:
        msg['To'] = ", ".join(email)
    else:
        msg['To'] = email
    s.sendmail(EMAIL_USER, email, msg.as_string())
    s.close()


def usernotfound_email(emails, host):
    s = smtplib.SMTP_SSL(host='smtp.gmail.com', port=465)
    s.ehlo()
    s.login(EMAIL_USER, EMAIL_PASSWORD)
    message = "There is an user not registered in Zabbix!\n\n"
    message = message + "Please, register this user: " + host + "\n"
    message = message + "More info you can find here: lmcad.com/zabbix"
    msg = MIMEText(message)
    msg['Subject'] = "URGENT: there is an user unregistered"
    msg['From'] = EMAIL_USER
    if type(emails) is list:
        msg['To'] = ", ".join(emails)
    else:
        msg['To'] = emails
    s.sendmail(EMAIL_USER, emails, msg.as_string())
    s.close()

def wastagequota(email, quota, wastage):
    s = smtplib.SMTP_SSL(host='smtp.gmail.com', port=465)
    s.ehlo()
    s.login(EMAIL_USER, EMAIL_PASSWORD)
    message = "You do not have more money to waste!\n\n"
    message = message + "Your quota is USD " + str(quota) + " and you have wasted USD " + str("%.2f" % round(wastage, 2)) + "\n"
    message = message + "You can ask more to admin"
    msg = MIMEText(message)
    msg['Subject'] = "URGENT: You do not have more money to waste!"
    msg['From'] = EMAIL_USER
    if type(email) is list:
        msg['To'] = ", ".join(email)
    else:
        msg['To'] = email
    print(msg)
    s.sendmail(EMAIL_USER, email, msg.as_string())
    s.close()
