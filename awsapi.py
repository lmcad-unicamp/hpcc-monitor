# -*- coding: utf-8 -*-
import logging
import os
import inspect
import re
import boto3 as boto
import botocore
from pprint import pprint
from datetime import datetime
import pytz

home = os.path.dirname(os.path.realpath(__file__))
logger = logging.getLogger(str(inspect.getouterframes(inspect.currentframe()
                                                      )[-1].filename))

REGION_AUTHORIZED_TO_GET_PRICING = 'us-east-1'
ACCESS_ID = (open(home+"/private/aws_access_key", "r")).read().strip('\n')
SECRET_KEY = (open(home+"/private/aws_secret_access_key", "r")
              ).read().strip('\n')

regions = {'us-east-1': "US East (N. Virginia)",
           'us-east-2': "US East (Ohio)",
           'us-west-1': "US West (N. California)",
           'us-west-2': "US West (Oregon)",
           'ap-east-1': "Asia Pacific (Hong Kong)",
           'ap-south-1': "Asia Pacific (Mumbai)",
           'ap-northeast-3': "Asia Pacific (Osaka-Local)",
           'ap-northeast-2': "Asia Pacific (Seoul)",
           'ap-southeast-1': "Asia Pacific (Singapore)",
           'ap-southeast-2': "Asia Pacific (Sydney)",
           'ap-northeast-1': "Asia Pacific (Tokyo)",
           'ca-central-1': "Canada (Central)",
           'eu-central-1': "Europe (Frankfurt)",
           'eu-west-1': "Europe (Ireland)",
           'eu-west-2': "Europe (London)",
           'eu-west-3': "Europe (Paris)",
           'eu-north-1': "Europe (Stockholm)",
           'me-south-1': "Middle East (Bahrain)",
           'sa-east-1': u"South America (São Paulo)"}

ebs_types = {'standard': 'Magnetic',
             'gp2': 'General Purpose',
             'io1': 'Provisioned IOPS',
             'st1': 'Throughput Optimized HDD',
             'sc1': 'Cold HDD'}

families = {'generalpurpose': ['m4', 'm5nd', 'm5n', 'm5ad', 'm5a', 'm5d',
                               'm5', 'm6g', 't2', 't3a', 't3', 'a1'],
            'compute': ['c4', 'c5n', 'c5d', 'c5'],
            'memory': ['z1d', 'u-', 'x1', 'r4', 'r5dn',
                       'r5n', 'r5ad', 'r5a', 'r5d', 'r5'],
            'accelerated': ['g3', 'g3s', 'g4dn', 'inf1', 'p2', 'p3dn', 'p3'],
            'storage': ['h1', 'd2', 'i3en', 'i3']}


# Get the family instance of a type
def get_instance_family(type):
    for family in families:
        for value in families[family]:
            if type.find(str(value)) != -1:
                return family


# Get operating system of a platform
def find_operatingsystem(instance_platform):
    if instance_platform.find("Linux/UNIX") != -1:
        return "Linux"
    elif instance_platform.find("Red Hat") != -1:
        return "RHEL"
    elif instance_platform.find("SUSE") != -1:
        return "SUSE"
    elif instance_platform.find("Windows") != -1:
        return "Windows"
    else:
        return "NA"


# Get license model of a platform
def find_licensemodel(instance_platform):
    if instance_platform.find("BYOL") != -1:
        return "Bring your own license"
    else:
        return "No License required"


# Get pre installed software of a platform
def find_preinstalledsoftware(instance_platform):
    if instance_platform.find("SQL") != -1:
        if instance_platform.find("Enterprise") != -1:
            return "SQL Ent"
        elif instance_platform.find("Standard") != -1:
            return "SQL Std"
        elif instance_platform.find("Web") != -1:
            return "SQL Web"
        else:
            return "SQL Web"
    else:
        return "NA"


# Get the price of a volume of a region
# You can use a volume info from a describe_volumes method of AWS client
# Or use a volume id
def get_volume_pricing(region, volume_info=None, volume_id=None):
    try:
        client = boto.client('ec2', region_name=region,
                             aws_access_key_id=ACCESS_ID,
                             aws_secret_access_key=SECRET_KEY)

    except botocore.exceptions.ClientError:
        return

    # If instance info is used
    if volume_info:
        volume_id = volume_info['VolumeId']
    # If a volume id is used, request client.describe_volume for infos
    elif volume_id:
        try:
            volume_info = client.describe_volumes(InstanceIds=[volume_id])
        except botocore.exceptions.ClientError as e:
            logger.error("[AWS] [get_volume_pricing] Volume could not "
                         + "found " + volume_id + ": " + str(e))
            return
        else:
            volume_info = volume_info['Volumes']
    # Else it is a error
    else:
        logger.error("[AWS] [get_volume_pricing] A volume_info or "
                     + "volume_id is needed")
        return

    volume_type = volume_info['VolumeType']
    volume_size = volume_info['Size']
    volume_location = re.sub(r'\D$', '', volume_info['AvailabilityZone'])

    # The price of products with these attributes is requested
    prices = boto.client('pricing',
                         region_name=REGION_AUTHORIZED_TO_GET_PRICING,
                         aws_access_key_id=ACCESS_ID,
                         aws_secret_access_key=SECRET_KEY)
    price = prices.get_products(ServiceCode='AmazonEC2', Filters=[
                                   {'Type': 'TERM_MATCH',
                                    'Field': 'volumeType',
                                    'Value': ebs_types[volume_type]},
                                   {'Type': 'TERM_MATCH',
                                    'Field': 'location',
                                    'Value': regions[volume_location]}])

    # If there is no product with these attributes
    if not price["PriceList"]:
        logger.error("[AWS] [get_volume_pricing] Price not found for "
                     + "volume " + volume_id)
        return

    # The price is
    try:
        volume_price = (list(list(eval(price["PriceList"][0])["terms"]
                                  ["OnDemand"].values())
                             [0]["priceDimensions"].values())
                        [0]["pricePerUnit"]["USD"])
    except (KeyError, IndexError) as e:
        logger.error("[AWS] [get_volume_pricing] Price not found for volume "
                     + volume_id + ": " + str(e))
        return

    # The price is the value per GB per month,
    # then we return the price per hour (if a month has 30 days)
    return float(volume_price)*float(volume_size)/720.0


# Get the price of an instance of a region
# You can use a instance info from a describe_instances method of AWS client
# Or use a instance id
def get_instance_pricing(region, instance_info=None, instance_id=None):
    try:
        client = boto.client('ec2', region_name=region,
                             aws_access_key_id=ACCESS_ID,
                             aws_secret_access_key=SECRET_KEY)
    except botocore.exceptions.ClientError:
        return

    # If instance info is used
    if instance_info:
        instance_id = instance_info['InstanceId']
    # If a instance id is used, request client.describe_instance for infos
    elif instance_id:
        try:
            instance_info = client.describe_instances(
                                            InstanceIds=[instance_id])
            # instance_info = client.describe_reserved_instances(
            #                               ReservedInstancesIds=[instance_id])
        except botocore.exceptions.ClientError as e:
            logger.error("[AWS] [get_instance_pricing] Instance could not "
                         + "found " + instance_id + ": " + str(e))
            return
        else:
            instance_info = instance_info['Reservations'][0]['Instances'][0]
    # Else it is a error
    else:
        logger.error("[AWS] [get_instance_pricing] A instance_info or "
                     + "instance_id is needed")
        return

    # Get instance type and region
    instance_type = instance_info['InstanceType']
    availability_zone = re.sub(r'\D$', '',
                               instance_info['Placement']['AvailabilityZone'])

    # Get tenancy, if it is default then we use Shared
    tenancy = instance_info['Placement']['Tenancy']
    if tenancy == "default":
        tenancy = 'Shared'

    # Get instance image infos
    image_id = instance_info['ImageId']
    image = client.describe_images(ImageIds=[image_id])

    if not image['Images']:
        logger.error("[AWS] [get_instance_pricing] Image " + str(image_id)
                     + " does not exist, using default information."
                     + " Instance " + instance_id)
        operating_system = 'Linux'
        preinstalled_sw = 'NA'
        license_model = 'No License required'
    else:
        # Find operating system, licesen model and pre installed softwares
        operating_system = find_operatingsystem(image['Images'][0]
                                                ['PlatformDetails'])
        license_model = find_licensemodel(image['Images'][0]
                                               ['PlatformDetails'])
        preinstalled_sw = find_preinstalledsoftware(image['Images'][0]
                                                    ['PlatformDetails'])

    # Since we are using the instance, the capacity status is Used
    capacity_status = 'Used'

    # If the type of the instance if one of these, there are some constants
    for f in ['c1', 'c3', 'g2', 'i2', 'm1', 'm2', 'm3', 'r3']:
        if instance_type.find(f) != -1:
            license_model = 'NA'
            operating_system = 'NA'
            capacity_status = 'NA'

    # If there is a capacity reservation that matches with the instance,
    # Then the capacity reservation is used
    capacityreservationflag = False
    if (instance_info['CapacityReservationSpecification']
            ['CapacityReservationPreference'] == 'open'):
        if ('CapacityReservationTarget' in
                instance_info['CapacityReservationSpecification']):
            # Get the id of capacity reservation and requires infos about
            capacity_id = (instance_info['CapacityReservationSpecification']
                           ['CapacityReservationTarget']
                           ['capacity_reservation_id'])
            capacity_reservation = client.describe_capacity_reservations(
                                        CapacityReservationIds=[capacity_id])
            # Since we are using the instance, the capacity status is Used
            capacity_status = 'Used'
            # The operating system and pre-installed sofware are defined
            operating_system = find_operatingsystem(capacity_reservation
                                                    ['InstancePlatform'])
            preinstalled_sw = find_preinstalledsoftware(capacity_reservation
                                                        ['InstancePlatform'])
            capacityreservationflag = True

    # The price of products with these attributes is requested
    prices = boto.client('pricing',
                         region_name=REGION_AUTHORIZED_TO_GET_PRICING,
                         aws_access_key_id=ACCESS_ID,
                         aws_secret_access_key=SECRET_KEY)
    price = prices.get_products(ServiceCode="AmazonEC2",
                                Filters=[{'Type': "TERM_MATCH",
                                          'Field': "servicecode",
                                          'Value': "AmazonEC2"},
                                         {'Type': "TERM_MATCH",
                                          'Field': "instanceType",
                                          'Value': instance_type},
                                         {'Type': "TERM_MATCH",
                                          'Field': "location",
                                          'Value': regions[availability_zone]},
                                         {'Type': "TERM_MATCH",
                                          'Field': "operatingSystem",
                                          'Value': operating_system},
                                         {'Type': "TERM_MATCH",
                                          'Field': "licenseModel",
                                          'Value': license_model},
                                         {'Type': "TERM_MATCH",
                                          'Field': "preInstalledSw",
                                          'Value': preinstalled_sw},
                                         {'Type': "TERM_MATCH",
                                          'Field': "tenancy",
                                          'Value': tenancy},
                                         {'Type': "TERM_MATCH",
                                          'Field': "capacitystatus",
                                          'Value': capacity_status}
                                         ])

    # If there is no product with these attributes
    if not price["PriceList"]:
        logger.error("[AWS] [get_instance_pricing] Price not found for "
                     + "instance " + instance_id)
        return

    # The On Demand price is
    if not capacityreservationflag:
        try:
            instance_price = (list(list(eval(price["PriceList"][0])["terms"]
                                        ["OnDemand"].values())
                                   [0]["priceDimensions"].values())
                              [0]["pricePerUnit"]["USD"])

        except (KeyError, IndexError) as e:
            logger.error("[AWS] [get_instance_pricing] Price not found for "
                         + "instance " + instance_id + ": " + str(e))
            return
    else:
        logger.error("[AWS] [get_instance_pricing] Capacity Reservation "
                     + "pricing not programmed. Instance: " + instance_id)
        return
    return float(instance_price)


# Get the price of a spot instance
def get_spotinstance_pricing(region, instance_info=None, instance_id=None):
    try:
        client = boto.client('ec2', region_name=region,
                             aws_access_key_id=ACCESS_ID,
                             aws_secret_access_key=SECRET_KEY)

    except botocore.exceptions.ClientError:
        return

    # If instance info is used
    if instance_info:
        instance_id = instance_info['InstanceId']
    # If a instance id is used, request client.describe_instance for infos
    elif instance_id:
        try:
            instance_info = client.describe_instances(
                                                    InstanceIds=[instance_id])
        except botocore.exceptions.ClientError as e:
            logger.error("[AWS] [get_spotinstance_pricing] Instance could not "
                         + "found " + instance_id + ": " + str(e))
            return
        else:
            instance_info = instance_info['Reservations'][0]['Instances'][0]
    # Else it is a error
    else:
        logger.error("[AWS] [get_spotinstance_pricing] A instance_info or "
                     + "instance_id is needed")
        return

    # Get instance type and region
    instance_type = instance_info['InstanceType']
    availability_zone = instance_info['Placement']['AvailabilityZone']

    # Get instance image infos
    image_id = instance_info['ImageId']
    image = client.describe_images(ImageIds=[image_id])

    if not image['Images']:
        logger.error("[AWS] [get_spotinstance_pricing] Image " + str(image_id)
                     + " does not exist, using default information."
                     + " Instance " + instance_id)
        operating_system = 'Linux'
    else:
        # Find operating system based on description of the image
        operating_system = find_operatingsystem(image['Images'][0]
                                                ['PlatformDetails'])

    # Get the last spot price based on instance type and region
    price = client.describe_spot_price_history(
            InstanceTypes=[instance_type],
            StartTime=datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            AvailabilityZone=availability_zone
            )

    # If there is no product with these attributes
    if not price['SpotPriceHistory']:
        logger.error("[AWS] [get_instance_pricing] Price not found for "
                     + "instance " + instance_id)
    else:
        # If there is no product with these attributes
        # It is returned prices for each platform, just need to find which one
        for product in price['SpotPriceHistory']:
            if (product['ProductDescription'].find('Windows') != -1
                    and operating_system == 'Windows'):
                instance_price = product['SpotPrice']
                break
            elif (product['ProductDescription'].find('SUSE') != -1
                    and operating_system == 'SUSE'):
                instance_price = product['SpotPrice']
                break
            elif (product['ProductDescription'].find('Red Hat') != -1
                    and operating_system == 'RHEL'):
                instance_price = product['SpotPrice']
                break
            elif (product['ProductDescription'].find('Linux') != -1
                    and operating_system == 'Linux'
                    and product['ProductDescription'].find('SUSE') == -1
                    and product['ProductDescription'].find('Red Hat') == -1):
                instance_price = product['SpotPrice']
                break
        if instance_price:
            return float(instance_price)
        else:
            logger.error("[AWS] [get_spotinstance_pricing] Could not find "
                         + "a platform that matches. Instance: "
                         + str(instance_id))
    return


# Print the pricing list of a list of product
def print_prices(products):
    for product in [eval(x) for x in products["PriceList"]]:
        pprint(product["product"]["attributes"]["instanceType"] + " "
               + product["product"]["attributes"]["location"] + " - "
               + product["product"]["attributes"]["operatingSystem"] + " - "
               + product["product"]["attributes"]["preInstalledSw"] + " - "
               + product["product"]["attributes"]["licenseModel"] + "      "
               + product["product"]["attributes"]["capacitystatus"] + " - "
               + product["product"]["attributes"]["tenancy"] + " "
               + list(product["terms"]["OnDemand"].values()
                      )[0]["priceDimensions"].values(
                      )[0]["pricePerUnit"]["USD"] + " "
               + list(product["terms"]["OnDemand"].values()
                      )[0]["priceDimensions"].values()[0]["unit"]
               )
        if len(product["terms"].values()) > 1:
            for i in range(len(list(product["terms"]["Reserved"].values()))):
                pprint("                                "
                       + list(product["terms"]["Reserved"].values()
                              )[i]["termAttributes"]["LeaseContractLength"]
                       + " "
                       + list(product["terms"]["Reserved"].values()
                              )[i]["termAttributes"]["OfferingClass"] + " "
                       + list(product["terms"]["Reserved"].values()
                              )[i]["termAttributes"]["PurchaseOption"])
                for j in range(len(list(product["terms"]["Reserved"].values()
                                        )[i]["priceDimensions"].values())):
                    pprint("                                                  "
                           + list(product["terms"]["Reserved"].values()
                                  )[i]["priceDimensions"].values(
                                  )[j]["pricePerUnit"]["USD"] + " "
                           + list(product["terms"]["Reserved"].values()
                                  )[i]["priceDimensions"].values()[j]["unit"])


def get_last_deattachment(region, volume):
    try:
        client = boto.client('cloudtrail', region_name=region,
                             aws_access_key_id=ACCESS_ID,
                             aws_secret_access_key=SECRET_KEY)
    except botocore.exceptions.ClientError as e:
        logger.error("[AWS] [get_last_attachment] Could not get history of"
                     + " volume " + volume + ": " + str(e))
    else:
        events = client.lookup_events(LookupAttributes=[{
                                            'AttributeKey': 'ResourceName',
                                            'AttributeValue': volume
                                            }])
        for e in events['Events']:
            if e['EventName'] == 'DetachVolume':
                return e['EventTime'].astimezone(pytz.utc)


# Get volumes from AWS
def get_volumes(pricing=False, ignore={}):
    volumes = []
    # For each region, we ask to the AWS API for volumes
    #for region in ['us-east-2']:
    for region in regions:
        try:
            client = boto.client('ec2', region_name=region,
                                 aws_access_key_id=ACCESS_ID,
                                 aws_secret_access_key=SECRET_KEY)
            clientvolumes = client.describe_volumes()
        except botocore.exceptions.ClientError:
            pass
        else:
            # For each instance, we get attributes from the it
            for volume in [i for i in clientvolumes['Volumes']]:
                v = {}

                tags = {item['Key']: item['Value'] for item in volume['Tags']}

                # Ignore instances with tags to ignore (argument)
                if 'tags' in ignore:
                    if [True for t in ignore['tags']
                       if t in tags and tags[t] in ignore['tags'][t]]:
                        continue

                v['user'] = tags['owner']
                v['attachments'] = None
                for a in volume['Attachments']:
                    if a['State'] == 'attached':
                        v['attachments'] = {}
                        v['attachments']['device'] = a['Device']
                        v['attachments']['instance'] = a['InstanceId']
                        v['attachments']['time'] = a['AttachTime'].astimezone(
                                                                    pytz.utc)
                v['deattachment'] = get_last_deattachment(region,
                                                          volume['VolumeId'])
                v['id'] = volume['VolumeId']
                v['type'] = volume['VolumeType']
                v['launchtime'] = volume['CreateTime'].astimezone(pytz.utc)
                v['state'] = volume['State']
                v['price'] = None
                if pricing:
                    v['price'] = get_volume_pricing(region, volume_info=volume)
                v['region'] = re.sub(r'\D$', '', volume['AvailabilityZone'])
                v['provider'] = 'aws'
                volumes.append(v)
    return volumes


# Get instances from AWS
# if you want to ignore some hosts, just add ignore argument is a dict
def get_instances(pricing=False, ignore={}):
    instances = []

    # For each region, we ask to the AWS API for instances
    #for region in ['us-east-1', 'us-east-2']:
    for region in regions:
        try:
            client = boto.client('ec2', region_name=region,
                                 aws_access_key_id=ACCESS_ID,
                                 aws_secret_access_key=SECRET_KEY)
            clientinstances = client.describe_instances()
        except botocore.exceptions.ClientError:
            pass
        else:
            # For each instance, we get attributes from the it
            for instance in [i['Instances'][0]
                             for i in clientinstances['Reservations']]:
                i = {}

                # Get the state of the instance
                i['state'] = instance['State']['Name']
                # Ignore instances with states to ignore (argument)
                if 'state' in ignore and i['state'] in ignore['state']:
                    continue

                # Get tags from instance
                tags = {item['Key']: item['Value']
                        for item in instance['Tags']}

                # Ignore instances with tags to ignore (argument)
                if 'tags' in ignore:
                    if [True for t in ignore['tags']
                       if t in tags and tags[t] in ignore['tags'][t]]:
                        continue

                # If it is spot
                if 'SpotInstanceRequestId' in instance:
                    i['service'] = 'spot'
                    i['service_id'] = instance['SpotInstanceRequestId']
                else:
                    i['service'] = 'ondemand'
                    i['service_id'] = instance['InstanceId']
                i['user'] = tags['owner']
                i['id'] = instance['InstanceId']
                i['type'] = instance['InstanceType']
                i['family'] = get_instance_family(instance['InstanceType'])
                i['launchtime'] = instance['LaunchTime'].astimezone(pytz.utc)
                i['provider'] = 'aws'

                # The region comes like 'us-east-1b',
                # we use regex to eliminate the final character
                i['region'] = re.sub(r'\D$', '',
                                     instance['Placement']['AvailabilityZone'])

                # Get price
                i['price'] = None
                if pricing:
                    ignorepricing = False
                    if 'price' in ignore:
                        for p in ignore['price']:
                            if i[p] in ignore['price'][p]:
                                ignorepricing = True
                    if not ignorepricing:
                        if i['service'] == 'ondemand':
                            i['price'] = get_instance_pricing(region,
                                                              instance_info
                                                              =instance)
                        elif i['service'] == 'spot':
                            i['price'] = get_spotinstance_pricing(region,
                                                                  instance_info
                                                                  =instance)
                instances.append(i)
    return instances
