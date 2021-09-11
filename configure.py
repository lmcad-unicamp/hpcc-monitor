"""
Authors: William Felipe C. Tavares, Marcio Roberto Miranda Assis, Edson Borin
Copyright Unicamp
"""
import os

keep = True
while keep:
    email_user = input('\t\tEnter the server email: ')
    email_password = input('\t\tEnter the server email password: ')
    ip_server = input('\t\tEnter the IP server: ')
    zabbix_user = input('\t\tEnter the Zabbix server user: ')
    zabbix_password = input('\t\tEnter the Zabbix server password: ')
    db_server = input('\t\tEnter the database server IP: ')
    db_user = input('\t\tEnter the database server user: ')
    db_password = input('\t\tEnter the database server password: ')
    website = input('\t\tEnter a website of informations: ')

    print('\t'+str(email_user))
    print('\t'+str(email_password))
    print('\t'+str(ip_server))
    print('\t'+str(zabbix_user))
    print('\t'+str(zabbix_password))
    print('\t'+str(db_server))
    print('\t'+str(db_user))
    print('\t'+str(db_password))
    print('\t'+str(website))
    keep = False
    right = input('\t\tIs everything right? (N)o or any other charactere: ')
    if right == 'N':
        keep = True
try:
    os.mkdir('log')
    print('\t'+str("Directory /log created"))
except Exception as e:
    print(e)
try:
    os.mkdir('files')
    print('\t'+str("Directory /files created"))
except Exception as e:
    print(e)
try:
    os.mkdir('private')
    print('\t'+str("Directory /private created"))
except Exception as e:
    print(e)

(open('private/email_user', 'w')).write(email_user)
(open('private/email_password', 'w')).write(email_password)
(open('private/ip_server', 'w')).write(ip_server)
(open('private/zabbix_user', 'w')).write(zabbix_user)
(open('private/zabbix_password', 'w')).write(zabbix_password)
(open('private/db_server', 'w')).write(db_server)
(open('private/db_user', 'w')).write(db_user)
(open('private/db_password', 'w')).write(db_password)
(open('private/website', 'w')).write(website)

print('\t' + 'Done!')
print('\t' + 'Now, insert your provider credentials')

keep = True
providers = []
while keep:
    provider = input("\t\tWhich provider do you want to add cretendials? "
                     + "(A)-Amazon Web Services "
                     + "(M)-Microsoft Azure "
                     + "(G)-Google Cloud")
    if provider == 'A':
        aws_access_key = input('\t\tEnter the AWS Access Key: ')
        aws_secret_access_key = input('\t\tEnter the AWS Secret Access Key: ')
        right = input('\t\tConfirm with Y. Cancel with any other charactere: ')
        if right == 'Y':
            print('\t'+str("Done!"))
            (open('private/aws_access_key', 'w'
                )).write(aws_access_key+'\n')
            (open('private/aws_secret_access_key', 'w'
                )).write(aws_secret_access_key+'\n')
            providers.append('aws')
    elif provider == 'M':
        print('\t'+str("Not developed yet"))

    elif provider == 'G':
        print('\t'+str("Not developed yet"))
    else:
        print('\t'+str("Does not match"))

    right = input('\t\tWant to add another provider? '
                  + '(N)o or any other charactere: ')
    if right == 'N':
        keep = False

providers = ['aws']
with open('private/providers', 'w') as providers_file:
    for p in providers:
        providers_file.write(p+'\n')

print('\t'+str("Alright, everything is saved on /private directory"
      + ", if is the case, you can change the information there."))
