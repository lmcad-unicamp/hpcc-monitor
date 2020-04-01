# -*- coding: utf-8 -*-
import os
import sys
import json
import boto3 as boto
from pprint import pprint
from datetime import datetime

regions = {'us-east-2': "US East (Ohio)", 'us-east-1': "US East (N. Virginia)",
           'us-west-1': "US West (N. California)", 'us-west-2': "US West (Oregon)",
           'ap-east-1': "Asia Pacific (Hong Kong)", 'ap-south-1': "Asia Pacific (Mumbai)",
           'ap-northeast-3': "Asia Pacific (Osaka-Local)", 'ap-northeast-2': "Asia Pacific (Seoul)",
           'ap-southeast-1': "Asia Pacific (Singapore)", 'ap-southeast-2' : "Asia Pacific (Sydney)",
           'ap-northeast-1': "Asia Pacific (Tokyo)", 'ca-central-1': "Canada (Central)",
           'eu-central-1': "Europe (Frankfurt)", 'eu-west-1': "Europe (Ireland)",
           'eu-west-2': "Europe (London)", 'eu-west-3': "Europe (Paris)",
           'eu-north-1': "Europe (Stockholm)", 'me-south-1': "Middle East (Bahrain)",
           'sa-east-1': u"South America (São Paulo)"}

families = {'generalpurpose': ['m4', 'm5nd', 'm5n', 'm5ad', 'm5a', 'm5d', 'm5', 'm6g', 't2', 't3a', 't3', 'a1'],
            'compute' : ['c4', 'c5n', 'c5d', 'c5'],
            'memory' : ['z1d', 'u-', 'x1', 'r4', 'r5dn', 'r5n', 'r5ad', 'r5a', 'r5d', 'r5'],
            'accelerated' : ['g3', 'g3s', 'g4dn', 'inf1', 'p2', 'p3dn', 'p3'],
            'storage' : ['h1', 'd2', 'i3en', 'i3']}

def getfamily(type):
    for key,value in families.iteritems():
        for t in value:
            if type.find(str(t)) != -1:
                return key

def findoperatingsystem(instance_platform, image_name):
    if instance_platform.find("Linux") != -1:
        return "Linux"
    elif instance_platform.find("Ubuntu") != -1:
        return "Linux"
    elif instance_platform.find("CentOS") != -1:
        return "Linux"
    elif instance_platform.find("Windows") != -1:
        return "Windows"
    elif instance_platform.find("Red Hat") != -1:
        return "RHEL"
    elif instance_platform.find("SUSE") != -1:
        return "SUSE"
    else:
        if image_name.find("Linux") != -1:
            return "Linux"
        elif image_name.find("Ubuntu") != -1:
            return "Linux"
        elif image_name.find("ubuntu") != -1:
            return "Linux"
        elif image_name.find("CentOS") != -1:
            return "Linux"
        elif image_name.find("Windows") != -1:
            return "Windows"
        elif image_name.find("Red Hat") != -1:
            return "RHEL"
        elif image_name.find("SUSE") != -1:
            return "SUSE"
        else:
            return "NA"

def findpreinstalledsoftware(instance_platform):
    if instance_platform.find("SQL") != -1:
        if instance_platform.find("Enterprise") != -1:
            return "SQL Ent"
        elif instance_platform.find("Standard") != -1:
            return "SQL Std"
        elif instance_platform.find("Web") != -1:
            return "SQL Web"
    else:
        return "NA"


def printPrices(price):
    for product in [ eval(x) for x in price["PriceList"] ]:
        pprint(product["product"]["attributes"]["instanceType"] + " " #sim
            + product["product"]["attributes"]["location"] + " - " #sim
            + product["product"]["attributes"]["operatingSystem"] + " - "
            + product["product"]["attributes"]["preInstalledSw"] + " - "
            + product["product"]["attributes"]["licenseModel"] + "      "
            + product["product"]["attributes"]["capacitystatus"] + " - " #sim
            + product["product"]["attributes"]["tenancy"] + " " #sim
            + product["terms"]["OnDemand"].values()[0]["priceDimensions"].values()[0]["pricePerUnit"]["USD"] + " "
            + product["terms"]["OnDemand"].values()[0]["priceDimensions"].values()[0]["unit"]
            )
        if len(product["terms"].values()) > 1:
            for i in range(len(product["terms"]["Reserved"].values())):
                pprint("                                "
                + product["terms"]["Reserved"].values()[i]["termAttributes"]["LeaseContractLength"] + " "
                + product["terms"]["Reserved"].values()[i]["termAttributes"]["OfferingClass"] + " "
                + product["terms"]["Reserved"].values()[i]["termAttributes"]["PurchaseOption"])
                for j in range(len(product["terms"]["Reserved"].values()[i]["priceDimensions"].values())):
                    pprint("                                                   "
                    + product["terms"]["Reserved"].values()[i]["priceDimensions"].values()[j]["pricePerUnit"]["USD"] + " "
                    + product["terms"]["Reserved"].values()[i]["priceDimensions"].values()[j]["unit"])

def getpricing(instance_id, ondemand=True, verbose=False):
    ACCESS_ID = (open(os.environ['HOME']+"/monitoring-system/private/aws_access_key", "r")).read()[:-1]
    SECRET_KEY = (open(os.environ['HOME']+"/monitoring-system/private/aws_secret_access_key", "r")).read()[:-1]

    client = boto.client('ec2', region_name='us-east-2', aws_access_key_id=ACCESS_ID, aws_secret_access_key=SECRET_KEY)
    ec2 = boto.resource('ec2', region_name='us-east-2', aws_access_key_id=ACCESS_ID, aws_secret_access_key=SECRET_KEY)

    if ondemand:
        INSTANCE_INFO = client.describe_instances(InstanceIds=[instance_id])
    else:
        INSTANCE_INFO = client.describe_reserved_instances(ReservedInstancesIds=[instance_id])

    instance_type = INSTANCE_INFO['Reservations'][0]['Instances'][0]['InstanceType']
    image_id = INSTANCE_INFO['Reservations'][0]['Instances'][0]['ImageId']
    image = client.describe_images(ImageIds=[image_id], aws_access_key_id=ACCESS_ID, aws_secret_access_key=SECRET_KEY)
    operating_system = findoperatingsystem(image['Images'][0]['Description'],image['Images'][0]['Name'])
    if operating_system == 'Windows':
        #Falta o Bring Your Own License
        license_model = 'No License required'
    else:
        license_model = 'No License required'
    preinstalled_sw = findpreinstalledsoftware(image['Images'][0]['Description'])
    availability_zone = INSTANCE_INFO['Reservations'][0]['Instances'][0]['Placement']['AvailabilityZone']
    tenancy = INSTANCE_INFO['Reservations'][0]['Instances'][0]['Placement']['Tenancy']
    if tenancy == "default":
        tenancy = 'Shared'
    capacity_status = 'Used'
    if INSTANCE_INFO['Reservations'][0]['Instances'][0]['CapacityReservationSpecification']['CapacityReservationPreference'] == 'open':
        if 'CapacityReservationTarget' in INSTANCE_INFO['Reservations'][0]['Instances'][0]['CapacityReservationSpecification']:
            capacity_id = INSTANCE_INFO['Reservations'][0]['Instances'][0]['CapacityReservationSpecification']['CapacityReservationTarget']['capacity_reservation_id']
            capacity_reservation = client.describe_capacity_reservations(CapacityReservationIds=[capacity_id])
            capacity_status = 'Used'
            operating_system = findoperatingsystem(capacity_reservation['InstancePlatform'])
            preinstalled_sw = findpreinstalledsoftware(capacity_reservation['InstancePlatform'])

    if 'SpotInstanceRequestId' in INSTANCE_INFO['Reservations'][0]['Instances'][0]:
        price=client.describe_spot_price_history(InstanceTypes=[str(instance_type)],
                                            StartTime=datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                                            AvailabilityZone=str(availability_zone)
                                            )

        for product in price['SpotPriceHistory']:
            instance_price = product['SpotPrice']
            if product['ProductDescription'].find('Windows') != -1 and operating_system == 'Windows':
                break
            elif product['ProductDescription'].find('SUSE') != -1 and operating_system == 'SUSE':
                break
            elif product['ProductDescription'].find('Red Hat') != -1 and operating_system == 'RHEL':
                break
            elif product['ProductDescription'].find('Linux') != -1 and operating_system == 'Linux' and product['ProductDescription'].find('SUSE') == -1 and product['ProductDescription'].find('Red Hat') == -1:
                break
        if verbose:
            print("SPOT: "+instance_type+" "+availability_zone+" - "+operating_system+" "+license_model+" - "+preinstalled_sw+" - "+tenancy+" "+capacity_status+" - "+instance_price)

    else:
        if not availability_zone[-1].isdigit():
            availability_zone = availability_zone[:-1]

        prices = boto.client('pricing', aws_access_key_id=ACCESS_ID, aws_secret_access_key=SECRET_KEY)
        price=prices.get_products(ServiceCode="AmazonEC2", aws_access_key_id=ACCESS_ID, aws_secret_access_key=SECRET_KEY,
                                Filters=[{'Type':"TERM_MATCH",'Field':"servicecode",'Value':"AmazonEC2"},
                                        {'Type':"TERM_MATCH",'Field':"instanceType",'Value':str(instance_type)},
                                        {'Type':"TERM_MATCH",'Field':"location",'Value':str(regions[str(availability_zone)])},
                                        {'Type':"TERM_MATCH",'Field':"operatingSystem",'Value':str(operating_system)},
                                        {'Type':"TERM_MATCH",'Field':"licenseModel",'Value':str(license_model)},
                                        {'Type':"TERM_MATCH",'Field':"preInstalledSw",'Value':str(preinstalled_sw)},
                                        {'Type':"TERM_MATCH",'Field':"tenancy",'Value':str(tenancy)},
                                        {'Type':"TERM_MATCH",'Field':"capacitystatus",'Value':str(capacity_status)}
                                        ])
        if not price["PriceList"]:
            if verbose:
                print("[PRICING] SOME ATTRIBUTE IS INCORRECT, THERE IS NO CONFIGURATION WITH THESE VALUES: "+instance_type+" "+availability_zone+" - "+operating_system+" "+license_model+" - "+preinstalled_sw+" - "+tenancy+" "+capacity_status+" - ")
            instance_price = 1.0
        elif ondemand:
            instance_price = eval(price["PriceList"][0])["terms"]["OnDemand"].values()[0]["priceDimensions"].values()[0]["pricePerUnit"]["USD"]
            if verbose:
                print("ONDEMAND: "+instance_type+" "+availability_zone+" - "+operating_system+" "+license_model+" - "+preinstalled_sw+" - "+tenancy+" "+capacity_status+" - "+instance_price)
        else:
            if verbose:
                print("RESERVED")
    return instance_price

def gettype(instance_id, ondemand=True, verbose=False):
    ACCESS_ID = (open(os.environ['HOME']+"/monitoring-system/private/aws_access_key", "r")).read()[:-1]
    SECRET_KEY = (open(os.environ['HOME']+"/monitoring-system/private/aws_secret_access_key", "r")).read()[:-1]

    client = boto.client('ec2', region_name='us-east-2', aws_access_key_id=ACCESS_ID, aws_secret_access_key=SECRET_KEY)

    if ondemand:
        INSTANCE_INFO = client.describe_instances(InstanceIds=[instance_id])
    else:
        INSTANCE_INFO = client.describe_reserved_instances(ReservedInstancesIds=[instance_id])

    instance_type = INSTANCE_INFO['Reservations'][0]['Instances'][0]['InstanceType']
    return instance_type
