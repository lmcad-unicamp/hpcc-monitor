import os

masterkeep = True
while masterkeep:
    keep = True
    while keep:
        email_user = raw_input('\t\tEnter the server email: ')
        keep = False
        right = raw_input('\t\t\tIs this email right? '+str(email_user)+' (N)o or any other charactere: ')
        if right == 'N':
            keep = True

    keep = True
    while keep:
        email_password = raw_input('\t\tEnter the server email password: ')
        keep = False
        right = raw_input('\t\t\tIs this password right? '+str(email_password)+' (N)o or any other charactere: ')
        if right == 'N':
            keep = True

    keep = True
    while keep:
        ip_server = raw_input('\t\tEnter the IP server: ')
        keep = False
        right = raw_input('\t\t\tIs this IP server right? '+str(ip_server)+' (N)o or any other charactere: ')
        if right == 'N':
            keep = True

    keep = True
    while keep:
        zabbix_user = raw_input('\t\tEnter the Zabbix server user: ')
        keep = False
        right = raw_input('\t\t\tIs this Zabbix server user right? '+str(zabbix_user)+' (N)o or any other charactere: ')
        if right == 'N':
            keep = True


    keep = True
    while keep:
        zabbix_password = raw_input('\t\tEnter the Zabbix server password: ')
        keep = False
        right = raw_input('\t\t\tIs this Zabbix server password right? '+str(zabbix_password)+' (N)o or any other charactere: ')
        if right == 'N':
            keep = True

    print
    print('\t'+str(email_user))
    print('\t'+str(email_password))
    print('\t'+str(ip_server))
    print('\t'+str(zabbix_user))
    print('\t'+str(zabbix_password))
    masterkeep=False
    right = raw_input('\t\tIs everything right? (N)o or any other charactere: ')
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
(open('private/email_user','w')).write(email_user+'\n')
(open('private/email_password','w')).write(email_password+'\n')
(open('private/ip_server','w')).write(ip_server+'\n')
(open('private/zabbix_user','w')).write(zabbix_user+'\n')
(open('private/zabbix_password','w')).write(zabbix_password+'\n')

print('\t'+str("Done!"))
print('\t'+str("Now, insert your provider credentials"))

keepmaster=True
while keepmaster:
    provider = raw_input("\t\tWhich provider do you want to add cretendials? (A)-Amazon Web Services (M)-Microsoft Azure (G)-Google Cloud")
    if provider == 'A':
        keep = True
        while keep:
            aws_access_key = raw_input('\t\tEnter the AWS Access Key: ')
            keep = False
            right = raw_input('\t\t\tIs this AWS Access Key right? '+str(aws_access_key)+' (N)o or any other charactere: ')
            if right == 'N':
                keep = True

        keep = True
        while keep:
            aws_secret_access_key = raw_input('\t\tEnter the AWS Secret Access Key: ')
            keep = False
            right = raw_input('\t\t\tIs this AWS Secret Access Key right? '+str(aws_secret_access_key)+' (N)o or any other charactere: ')
            if right == 'N':
                keep = True

        print
        print('\t'+str("Done!"))
        (open('private/aws_access_key','w')).write(aws_access_key+'\n')
        (open('private/aws_secret_access_key','w')).write(aws_secret_access_key+'\n')
    elif provider == 'M':
        print('\t'+str("Not developed yet"))

    elif provider == 'G':
        print('\t'+str("Not developed yet"))
    else:
        print('\t'+str("Does not match"))

    right = raw_input('\t\tWant to add another provider? (N)o or any other charactere: ')
    if right == 'N':
        keepmaster = False

print('\t'+str("Alright, everything is saved on /private directory, if is the case, you can change the information there."))
