import os
import zapi as z
from sendemail import user_registered
import getpass
import MySQLdb

keep = True
while keep:
    user_name = input('\t\tEnter the user name: ')
    user_password = getpass.getpass('\t\tEnter a password: ')
    name = input('\t\tEnter the First Name: ')
    surname = input('\t\tEnter the Surname: ')
    user_email = input('\t\tEnter the email: ')
    quota = input('\t\tEnter the quota: ')

    print('\t'+str(user_name))
    print('\t'+str(name))
    print('\t'+str(surname))
    print('\t'+str(user_email))
    print('\t'+str(quota))
    keep = False
    right = input('\t\tIs everything right? (N)o or any other charactere: ')
    right2 = input('\t\tRemember, username must be the same as the provider')
    if right == 'N' or right2 == 'N':
        keep = True

try:
    hostgroupid = z.zapi.hostgroup.create(name='user-'+user_name+'-hosts')
    hostgroupid = hostgroupid['groupids'][0]
    rights = z.zapi.usergroup.get(usrgrpids=['14'],
                                  selectRights=['id', 'permission'])
    rights = rights[0]['rights']
    rights.append({'id': hostgroupid, 'permission': '2'})
    z.zapi.usergroup.update(usrgrpid=14, rights=rights)
except z.pyzabbix.ZabbixAPIException as e:
    print(e)
    exit(1)

try:
    z.zapi.user.create(alias=user_name, name=name, surname=surname,
                       passwd=user_password, usrgrps=[{'usrgrpid': '14'}],
                       user_medias=[{'mediatypeid': '1',
                                     'sendto': user_email,
                                     'active': 0, 'severity':63,
                                     'period': '1-7,00:00-24:00'}])
except z.pyzabbix.ZabbixAPIException as e:
    print(e)
    exit(1)

try:
    z.zapi.usermacro.createglobal(macro="{$QUOTA_"+str(user_name).upper()+"}",
                                  value=str(quota))
except z.pyzabbix.ZabbixAPIException as e:
    print(e)

try:
    z.zapi.action.create(name=str(user_name).upper()
                         + ': GPU driver missing in host',
                         eventsource=0,
                         esc_period='1h',
                         def_shortdata='Problem: {EVENT.NAME}',
                         def_longdata='Problem started at {EVENT.TIME} '
                                      + 'on {EVENT.DATE}\r\nProblem name: '
                                      + '{EVENT.NAME}\r\nHost: {HOST.NAME}\r'
                                      + '\nSeverity: {EVENT.SEVERITY}\r\n\r'
                                      + '\nOriginal problem ID: {EVENT.ID}\r'
                                      + '\n{TRIGGER.URL}',
                         ack_shortdata='Updated problem: {EVENT.NAME}',
                         ack_longdata='{USER.FULLNAME} {EVENT.UPDATE.ACTION} '
                                      + 'problem at {EVENT.UPDATE.DATE} '
                                      + '{EVENT.UPDATE.TIME}.\r\n'
                                      + '{EVENT.UPDATE.MESSAGE}\r\n\r\n'
                                      + 'Current problem status is '
                                      + '{EVENT.STATUS}, acknowledged: '
                                      + '{EVENT.ACK.STATUS}.',
                         r_shortdata='Resolved: {EVENT.NAME}',
                         r_longdata='Problem has been resolved at '
                                    + '{EVENT.RECOVERY.TIME} on '
                                    + '{EVENT.RECOVERY.DATE}\r\nProblem name: '
                                    + '{EVENT.NAME}\r\nHost: {HOST.NAME}\r\n'
                                    + 'Severity: {EVENT.SEVERITY}\r\n\r\n'
                                    + 'Original problem ID: {EVENT.ID}\r\n'
                                    + '{TRIGGER.URL}',
                         filter={'evaltype': '1',
                                 'conditions': [{'operator': '0',
                                                 'conditiontype': '2',
                                                 'value': '16023'},
                                                {'operator': '0',
                                                 'conditiontype': '0',
                                                 'value': str(hostgroupid)}]
                                 },
                         operations=[
                                {'opmessage_usr': [{'userid':
                                                    z.getUserID(user_name)}],
                                    'operationtype': '0',
                                    'esc_period': '0',
                                    'evaltype': '0',
                                    'opmessage': {'mediatypeid': '1',
                                                  'default_msg': '1'},
                                    'esc_step_to': '1',
                                    'esc_step_from': '1'},
                                {'opmessage_grp': [{'usrgrpid': '16'}],
                                    'operationtype': '0',
                                    'esc_period': '0',
                                    'evaltype': '0',
                                    'opmessage': {'mediatypeid': '1',
                                                  'default_msg': '1'},
                                    'esc_step_to': '2',
                                    'esc_step_from': '2'}
                                ],
                         recovery_operations=[{'operationtype': '11',
                                              'opmessage': {
                                                    'mediatypeid': '1',
                                                    'default_msg': '1'}}]
                         )
except z.pyzabbix.ZabbixAPIException as e:
    print(e)

try:
    z.zapi.action.create(name=str(user_name).upper()
                         + ': GPU stopped sending data',
                         eventsource=0,
                         esc_period='1h',
                         def_shortdata='Problem: {EVENT.NAME}',
                         def_longdata='Problem started at {EVENT.TIME} on '
                                      + '{EVENT.DATE}\r\nProblem name: '
                                      + '{EVENT.NAME}\r\nHost: {HOST.NAME}\r\n'
                                      + 'Severity: {EVENT.SEVERITY}\r\n\r\n'
                                      + 'Original problem ID: {EVENT.ID}\r\n'
                                      + '{TRIGGER.URL}',
                         ack_shortdata='Updated problem: {EVENT.NAME}',
                         ack_longdata='{USER.FULLNAME} {EVENT.UPDATE.ACTION} '
                                      + 'problem at {EVENT.UPDATE.DATE} '
                                      + '{EVENT.UPDATE.TIME}.\r\n'
                                      + '{EVENT.UPDATE.MESSAGE}\r\n\r\n'
                                      + 'Current problem status is '
                                      + '{EVENT.STATUS}, acknowledged: '
                                      + '{EVENT.ACK.STATUS}.',
                         r_shortdata='Resolved: {EVENT.NAME}',
                         r_longdata='Problem has been resolved at '
                                    + '{EVENT.RECOVERY.TIME} on '
                                    + '{EVENT.RECOVERY.DATE}\r\n'
                                    + 'Problem name: {EVENT.NAME}\r\n'
                                    + 'Host: {HOST.NAME}\r\n'
                                    + 'Severity: {EVENT.SEVERITY}\r\n\r\n'
                                    + 'Original problem ID: {EVENT.ID}\r\n'
                                    + '{TRIGGER.URL}',
                         filter={'evaltype': '1',
                                 'conditions': [{'operator': '0',
                                                 'conditiontype': '2',
                                                 'value': '16097'},
                                                {'operator': '0',
                                                 'conditiontype': '0',
                                                 'value': str(hostgroupid)}]
                                 },
                         operations=[
                                {'opmessage_usr': [{'userid':
                                                    z.getUserID(user_name)}],
                                    'operationtype': '0',
                                    'esc_period': '0',
                                    'evaltype': '0',
                                    'opmessage': {'mediatypeid': '1',
                                                  'default_msg': '1'},
                                    'esc_step_to': '1',
                                    'esc_step_from': '1'},
                                {'opmessage_grp': [{'usrgrpid': '16'}],
                                    'operationtype': '0',
                                    'esc_period': '0',
                                    'evaltype': '0',
                                    'opmessage': {'mediatypeid': '1',
                                                  'default_msg': '1'},
                                    'esc_step_to': '2',
                                    'esc_step_from': '2'}
                                ],
                         recovery_operations=[{'operationtype': '11',
                                               'opmessage': {
                                                        'mediatypeid': '1',
                                                        'default_msg': '1'}}]
                            )
except z.pyzabbix.ZabbixAPIException as e:
    print(e)


try:
    z.zapi.action.create(name=str(user_name).upper()
                         + ': No data detected from host',
                         eventsource=0,
                         esc_period='1h',
                         def_shortdata='Problem: {EVENT.NAME}',
                         def_longdata='Problem started at {EVENT.TIME} on '
                                      + '{EVENT.DATE}\r\n'
                                      + 'Problem name: {EVENT.NAME}\r\n'
                                      + 'Host: {HOST.NAME}\r\n'
                                      + 'Severity: {EVENT.SEVERITY}\r\n\r\n'
                                      + 'Original problem ID: {EVENT.ID}\r\n'
                                      + '{TRIGGER.URL}',
                         ack_shortdata='Updated problem: {EVENT.NAME}',
                         ack_longdata='{USER.FULLNAME} {EVENT.UPDATE.ACTION} '
                                      + 'problem at {EVENT.UPDATE.DATE} '
                                      + '{EVENT.UPDATE.TIME}.\r\n'
                                      + '{EVENT.UPDATE.MESSAGE}\r\n\r\n'
                                      + 'Current problem status is '
                                      + '{EVENT.STATUS}, acknowledged: '
                                      + '{EVENT.ACK.STATUS}.',
                         r_shortdata='Resolved: {EVENT.NAME}',
                         r_longdata='Problem has been resolved at '
                                    + '{EVENT.RECOVERY.TIME} on '
                                    + '{EVENT.RECOVERY.DATE}\r\n'
                                    + 'Problem name: {EVENT.NAME}\r\n'
                                    + 'Host: {HOST.NAME}\r\n'
                                    + 'Severity: {EVENT.SEVERITY}\r\n\r\n'
                                    + 'Original problem ID: {EVENT.ID}\r\n'
                                    + '{TRIGGER.URL}',
                         filter={'evaltype': '1',
                                 'conditions': [{'operator': '0',
                                                 'conditiontype': '2',
                                                 'value': '16040'},
                                                {'operator': '0',
                                                 'conditiontype': '0',
                                                 'value': str(hostgroupid)}]
                                 },
                         operations=[
                                {'opmessage_usr': [{'userid':
                                                    z.getUserID(user_name)}],
                                    'operationtype': '0',
                                    'esc_period': '0',
                                    'evaltype': '0',
                                    'opmessage': {'mediatypeid': '1',
                                                  'default_msg': '1'},
                                    'esc_step_to': '1',
                                    'esc_step_from': '1'},
                                {'opmessage_grp': [{'usrgrpid': '16'}],
                                    'operationtype': '0',
                                    'esc_period': '0',
                                    'evaltype': '0',
                                    'opmessage': {'mediatypeid': '1',
                                                  'default_msg': '1'},
                                    'esc_step_to': '2',
                                    'esc_step_from': '2'}
                                ],
                         recovery_operations=[{'operationtype': '11',
                                               'opmessage': {
                                                       'mediatypeid': '1',
                                                       'default_msg': '1'}}]
                            )
except z.pyzabbix.ZabbixAPIException as e:
    print(e)

home = os.path.dirname(os.path.realpath(__file__))
DBSERVER = (open(home+"/private/db_server", "r")).read().strip('\n')
DBUSER = (open(home+"/private/db_user", "r")).read().strip('\n')
DBPASSWORD = (open(home+"/private/db_password", "r")).read().strip('\n')
con = MySQLdb.connect(DBSERVER, DBUSER, DBPASSWORD)
con.select_db('db_quota_manager')
cursor = con.cursor()
cursor.execute("INSERT INTO User_Wastage(UserName,Quota) VALUES(\""
               + str(user_name) + "\"," + str(float(quota)) + ")")
con.commit()


user_registered(user_email, user_name)
