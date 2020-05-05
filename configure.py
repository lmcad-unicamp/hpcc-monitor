import os

masterkeep = True
while masterkeep:
    keep = True
    while keep:
        email_user = input('\t\tEnter the server email: ')
        keep = False
        right = input('\t\t\tIs this email right? '+str(email_user)+' (N)o or any other charactere: ')
        if right == 'N':
            keep = True

    keep = True
    while keep:
        email_password = input('\t\tEnter the server email password: ')
        keep = False
        right = input('\t\t\tIs this password right? '+str(email_password)+' (N)o or any other charactere: ')
        if right == 'N':
            keep = True

    keep = True
    while keep:
        ip_server = input('\t\tEnter the IP server: ')
        keep = False
        right = input('\t\t\tIs this IP server right? '+str(ip_server)+' (N)o or any other charactere: ')
        if right == 'N':
            keep = True

    keep = True
    while keep:
        zabbix_user = input('\t\tEnter the Zabbix server user: ')
        keep = False
        right = input('\t\t\tIs this Zabbix server user right? '+str(zabbix_user)+' (N)o or any other charactere: ')
        if right == 'N':
            keep = True


    keep = True
    while keep:
        zabbix_password = input('\t\tEnter the Zabbix server password: ')
        keep = False
        right = input('\t\t\tIs this Zabbix server password right? '+str(zabbix_password)+' (N)o or any other charactere: ')
        if right == 'N':
            keep = True

    keep = True
    while keep:
        db_server = input('\t\tEnter the database server IP: ')
        keep = False
        right = input('\t\t\tIs this database server IP right? '+str(db_server)+' (N)o or any other charactere: ')
        if right == 'N':
            keep = True

    keep = True
    while keep:
        db_user = input('\t\tEnter the database server user: ')
        keep = False
        right = input('\t\t\tIs this database server user right? '+str(db_user)+' (N)o or any other charactere: ')
        if right == 'N':
            keep = True

    keep = True
    while keep:
        db_password = input('\t\tEnter the database server password: ')
        keep = False
        right = input('\t\t\tIs this database server password right? '+str(db_password)+' (N)o or any other charactere: ')
        if right == 'N':
            keep = True

    print('\t'+str(email_user))
    print('\t'+str(email_password))
    print('\t'+str(ip_server))
    print('\t'+str(zabbix_user))
    print('\t'+str(zabbix_password))
    print('\t'+str(db_server))
    print('\t'+str(db_user))
    print('\t'+str(db_password))
    masterkeep=False
    right = input('\t\tIs everything right? (N)o or any other charactere: ')
    if right == 'N':
        masterkeep = True
try:
    os.mkdir('log')
    print('\t'+str("Directory /log created"))
except:
    pass
try:
    os.mkdir('files')
    print('\t'+str("Directory /files created"))
except:
    pass
try:
    os.mkdir('private')
    print('\t'+str("Directory /private created"))
except:
    pass
(open('private/email_user','w')).write(email_user)
(open('private/email_password','w')).write(email_password)
(open('private/ip_server','w')).write(ip_server)
(open('private/zabbix_user','w')).write(zabbix_user)
(open('private/zabbix_password','w')).write(zabbix_password)
(open('private/db_server','w')).write(db_server)
(open('private/db_user','w')).write(db_user)
(open('private/db_password','w')).write(db_password)

print('\t'+str("Done!"))
print('\t'+str("Now, insert your provider credentials"))

keepmaster=True
while keepmaster:
    provider = input("\t\tWhich provider do you want to add cretendials? (A)-Amazon Web Services (M)-Microsoft Azure (G)-Google Cloud")
    if provider == 'A':
        keep = True
        while keep:
            aws_access_key = input('\t\tEnter the AWS Access Key: ')
            keep = False
            right = input('\t\t\tIs this AWS Access Key right? '+str(aws_access_key)+' (N)o or any other charactere: ')
            if right == 'N':
                keep = True

        keep = True
        while keep:
            aws_secret_access_key = input('\t\tEnter the AWS Secret Access Key: ')
            keep = False
            right = input('\t\t\tIs this AWS Secret Access Key right? '+str(aws_secret_access_key)+' (N)o or any other charactere: ')
            if right == 'N':
                keep = True

        print('\t'+str("Done!"))
        (open('private/aws_access_key','w')).write(aws_access_key+'\n')
        (open('private/aws_secret_access_key','w')).write(aws_secret_access_key+'\n')
    elif provider == 'M':
        print('\t'+str("Not developed yet"))

    elif provider == 'G':
        print('\t'+str("Not developed yet"))
    else:
        print('\t'+str("Does not match"))

    right = input('\t\tWant to add another provider? (N)o or any other charactere: ')
    if right == 'N':
        keepmaster = False

print('\t'+str("Alright, everything is saved on /private directory, if is the case, you can change the information there."))
