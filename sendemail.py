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
    message = message + ", more info you can get here: lmcad.com/agentinstallation"
    msg = MIMEText(message)
    msg['Subject'] = "URGENT: there is a host unregistered"
    msg['From'] = EMAIL_USER
    msg['To'] = ", ".join(emails)
    s.sendmail(EMAIL_USER, emails, msg.as_string())
    s.close()
