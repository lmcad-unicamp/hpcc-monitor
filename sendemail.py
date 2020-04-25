import smtplib
import os
from email.mime.text import MIMEText
home=os.path.dirname(os.path.realpath(__file__))

EMAIL_USER= (open(home+"/private/email_user", "r")).read()[:-1]
EMAIL_PASSWORD= (open(home+"/private/email_password", "r")).read()[:-1]

def alert_email(emails, host):
    s = smtplib.SMTP_SSL(host='smtp.gmail.com', port=465)
    s.ehlo()
    s.login(EMAIL_USER, EMAIL_PASSWORD)
    message = "WARNING: YOU HAVE AN INSTANCE THAT IS NOT BEING MONITORED!\n\n"
    message = message + "Please, install the agent in your instance (" + host + ")"
    message = message + ", more info you can get here: lmcad.com/zabbix"
    msg = MIMEText(message)
    msg['Subject'] = "URGENT: there is a host unregistered"
    msg['From'] = EMAIL_USER
    msg['To'] = ", ".join(emails)
    s.sendmail(EMAIL_USER, emails, msg.as_string())
    s.close()

def registered_email(email, username):
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
    msg['To'] = ", ".join(email)
    s.sendmail(EMAIL_USER, email, msg.as_string())
    s.close()

def usernotfound_email(emails, host):
    s = smtplib.SMTP_SSL(host='smtp.gmail.com', port=465)
    s.ehlo()
    s.login(EMAIL_USER, EMAIL_PASSWORD)
    message = "There is an user not registered in Zabbix!\n\n"
    message = message + "Please, register this user: " + host + "\n"
    message = message + "More info you can get here: lmcad.com/zabbix"
    msg = MIMEText(message)
    msg['Subject'] = "URGENT: there is an user unregistered"
    msg['From'] = EMAIL_USER
    msg['To'] = ", ".join(emails)
    s.sendmail(EMAIL_USER, emails, msg.as_string())
    s.close()
