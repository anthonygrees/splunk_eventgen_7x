from __future__ import division
import datetime
import time
import re
import random
import calendar
from xml.sax.saxutils import escape
import billing_utils as billing_utils
import billing_fixture as billing_fixture
from outputplugin import OutputPlugin


class BaseMonthlyBilling(OutputPlugin):
    name = 'aws_billing_monthly_base'
    MAXQUEUELENGTH = 10

    sample_account_total = "InvoiceID=#INVOICE_ID#, PayerAccountId=#PAYER_ID#, LinkedAccountId=#LINKED_ACCOUNT_ID#, RecordType=AccountTotal, RecordID=AccountTotal, BillingPeriodStartDate=#START_YMD# 00:00:00, BillingPeriodEndDate=#END_YMD# 23:59:59, InvoiceDate=, PayerAccountName=ABC Inc, LinkedAccountName=#LINKED_ACCOUNT_NAME#, TaxationAddress=, PayerPONumber=, ProductCode=, ProductName=, SellerOfRecord=, UsageType=, Operation=, RateId=, ItemDescription=Total for linked account# #LINKED_ACCOUNT_ID# (#LINKED_ACCOUNT_NAME#), UsageStartDate=#START_YMD#, UsageEndDate=#END_YMD#, UsageQuantity=, BlendedRate=, CurrencyCode=USD, CostBeforeTax=#COST#, Credits=0.0, TaxAmount=0, TaxType=, TotalCost=#COST#, S3KeyLastModified=#NOW#"
    sample_statement_total = "InvoiceID=#INVOICE_ID#, PayerAccountId=#PAYER_ID#, LinkedAccountId=, RecordType=StatementTotal, RecordID=StatementTotal, BillingPeriodStartDate=#START_YMD# 00:00:00, BillingPeriodEndDate=#END_YMD# 23:59:59, InvoiceDate=, PayerAccountName=ABC Inc, LinkedAccountName=, TaxationAddress=, PayerPONumber=, ProductCode=, ProductName=, SellerOfRecord=, UsageType=, Operation=, RateId=, ItemDescription=Total statement amount for period #START_YMD# 00:00:00 - #END_YMD# 23:59:59, UsageStartDate=#START_YMD#, UsageEndDate=#END_YMD#, UsageQuantity=, BlendedRate=, CurrencyCode=USD, CostBeforeTax=#COST#, Credits=0.0, TaxAmount=0, TaxType=, TotalCost=#COST#, S3KeyLastModified=#NOW#"

    # list of billing items and sample cost
    sample_billing_items = [
        #"ProductCode","ProductName","UsageType","ItemDescription","price","UsageQuantity","TotalCost"
        ["AmazonCloudFront","Amazon CloudFront","AP-DataTransfer-Out-Bytes","$0.190 per GB - first 10 TB / month data transfer out","0.19","800","151.3439"],
        ["AmazonCloudFront","Amazon CloudFront","AP-DataTransfer-Out-OBytes","$0.060 per GB - All data transfer out to Origin (Asia)","0.06","0","0.000001"],
        ["AmazonCloudFront","Amazon CloudFront","AP-Requests-HTTPS-Proxy","$0.0120 per 10,000 Proxy HTTPS Requests (Asia)","0.012","14140","0.0169"],
        ["AmazonCloudFront","Amazon CloudFront","AP-Requests-Tier2-HTTPS","$0.012 per 10,000 HTTPS Requests","0.012","1470","0.0017"],
        ["AWSDataTransfer","AWS Data Transfer","APN1-APS1-AWS-Out-Bytes","$0.09 per GB - Asia Pacific (Tokyo) data transfer to Asia Pacific (Singapore)","0.09","0","0.000001"],
        ["AWSDataTransfer","AWS Data Transfer","APN1-APS2-AWS-In-Bytes","$0.00 per GB - Asia Pacific (Tokyo) data transfer from Asia Pacific (Sydney)","0","0","0"],
        ["AWSDataTransfer","AWS Data Transfer","APN1-APS2-AWS-Out-Bytes","$0.09 per GB - Asia Pacific (Tokyo) data transfer to Asia Pacific (Sydney)","0.09","0","0"],
        ["AmazonSimpleDB","Amazon SimpleDB","APN1-BoxUsage","$0.00 per Compute-Hour consumed first 25 hours per month","0","0.1","0"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","APN1-BoxUsage:c3.2xlarge","$0.511 per On Demand Linux c3.2xlarge Instance Hour","0.511","52.5","26.8275"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","APN1-BoxUsage:m1.large","$0.243 per On Demand Linux m1.large Instance Hour","0.243","20.3","4.9329"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","APN1-BoxUsage:m1.large","$0.353 per On Demand Windows m1.large Instance Hour","0.353","3.5","1.2355"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","APN1-BoxUsage:m1.xlarge","$0.706 per On Demand Windows m1.xlarge Instance Hour","0.706","1.4","0.9884"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","APN1-BoxUsage:m3.xlarge","$0.405 per On Demand Linux m3.xlarge Instance Hour","0.405","467.6","189.378"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","APN1-BoxUsage:m3.xlarge","$0.603 per On Demand Windows m3.xlarge Instance Hour","0.603","19.6","11.8188"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","APN1-BoxUsage:t1.micro","$0.026 per On Demand Linux t1.micro Instance Hour","0.026","971.6","25.2616"],
        ["AWSDataTransfer","AWS Data Transfer","APN1-CloudFront-In-Bytes","$0.00 per GB data transfer in to Asia Pacific (Tokyo) from CloudFront","0","0","0"],
        ["AWSDataTransfer","AWS Data Transfer","APN1-CloudFront-Out-Bytes","$0.09 per GB data transfer out of Asia Pacific (Tokyo) to CloudFront","0.09","0","0.000001"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","APN1-CW:Requests","$0.01 per 1,000 requests","0.01","16051.7","0.160517"],
        ["AWSDataTransfer","AWS Data Transfer","APN1-DataTransfer-In-Bytes","$0.000 per GB - data transfer in per month","0","0","0"],
        ["AWSDataTransfer","AWS Data Transfer","APN1-DataTransfer-Out-Bytes","$0.000 per GB - first 1 GB of data transferred out per month","0","0.1","0"],
        ["AWSDataTransfer","AWS Data Transfer","APN1-DataTransfer-Regional-Bytes","$0.010 per GB - regional data transfer - in/out/between EC2 AZs or using IPs or ELB","0.01","0","0.000002"],
        ["AmazonSNS","Amazon Simple Notification Service","APN1-DeliveryAttempts-SQS","There is no charge for SQS Notifications","0","2455.6","0"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","APN1-EBS:SnapshotUsage","$0.095 per GB-Month of snapshot data stored - Asia Pacific (Tokyo)","0.095","0.2","0.023524"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","APN1-EBS:VolumeUsage","$0.08 per GB-month of Magnetic provisioned storage - Asia Pacific (Tokyo)","0.08","10.4","0.834581"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","APN1-EBS:VolumeUsage.gp2","$0.12 per GB-month of General Purpose (SSD) provisioned storage - Asia Pacific (Tokyo)","0.12","82.6","9.914032"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","APN1-ElasticIP:IdleAddress","$0.005 per Elastic IP address not attached to a running instance per hour (prorated)","0.005","485.8","2.4255"],
        ["AWSDataTransfer","AWS Data Transfer","APN1-EU-AWS-In-Bytes","$0.00 per GB - Asia Pacific (Tokyo) data transfer from EU (Ireland)","0","0","0"],
        ["AWSDataTransfer","AWS Data Transfer","APN1-EU-AWS-Out-Bytes","$0.09 per GB - Asia Pacific (Tokyo) data transfer to EU (Ireland)","0.09","0","0.000001"],
        ["AmazonS3","Amazon Simple Storage Service","APN1-Requests-Tier1","$0.0047 per 1,000 PUT, COPY, POST, or LIST requests","0.0047","0.7","0.000003"],
        ["AmazonSNS","Amazon Simple Notification Service","APN1-Requests-Tier1","First 1,000,000 Amazon SNS API Requests per month are free","0","8257.9","0"],
        ["AWSQueueService","Amazon Simple Queue Service","APN1-Requests-Tier1","First 1,000,000 Amazon SQS Requests per month are free","0","651","0"],
        ["AmazonS3","Amazon Simple Storage Service","APN1-Requests-Tier2","$0.0037 per 10,000 GET and all other requests","0.0037","0.7","0"],
        ["AWSDataTransfer","AWS Data Transfer","APN1-SAE1-AWS-In-Bytes","$0.00 per GB - Asia Pacific (Tokyo) data transfer from South America (Sao Paulo)","0","0","0"],
        ["AWSDataTransfer","AWS Data Transfer","APN1-SAE1-AWS-Out-Bytes","$0.09 per GB - Asia Pacific (Tokyo) data transfer to South America (Sao Paulo)","0.09","0","0"],
        ["AmazonS3","Amazon Simple Storage Service","APN1-TimedStorage-ByteHrs","$0.0330 per GB - first 1 TB / month of storage used","0.033","7.4","0.244633"],
        ["AWSDataTransfer","AWS Data Transfer","APN1-USE1-AWS-In-Bytes","$0.00 per GB - Asia Pacific (Tokyo) data transfer from US East (Northern Virginia)","0","0","0"],
        ["AWSDataTransfer","AWS Data Transfer","APN1-USE1-AWS-Out-Bytes","$0.09 per GB - Asia Pacific (Tokyo) data transfer to US East (Northern Virginia)","0.09","0","0.000005"],
        ["AWSDataTransfer","AWS Data Transfer","APN1-USW1-AWS-Out-Bytes","$0.09 per GB - Asia Pacific (Tokyo) data transfer to US West (Northern California)","0.09","0","0.000001"],
        ["AWSDataTransfer","AWS Data Transfer","APN1-USW2-AWS-In-Bytes","$0.00 per GB - Asia Pacific (Tokyo) data transfer from US West (Oregon)","0","0","0"],
        ["AWSDataTransfer","AWS Data Transfer","APS1-APN1-AWS-In-Bytes","$0.00 per GB - Asia Pacific (Singapore) data transfer from Asia Pacific (Tokyo)","0","0","0"],
        ["AWSDataTransfer","AWS Data Transfer","APS1-APS2-AWS-In-Bytes","$0.00 per GB - Asia Pacific (Singapore) data transfer from Asia Pacific (Sydney)","0","0","0"],
        ["AWSDataTransfer","AWS Data Transfer","APS1-APS2-AWS-Out-Bytes","$0.09 per GB - Asia Pacific (Singapore) data transfer to Asia Pacific (Sydney)","0.09","0","0.000036"],
        ["AmazonSimpleDB","Amazon SimpleDB","APS1-BoxUsage","$0.00 per Compute-Hour consumed first 25 hours per month","0","0.1","0"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","APS1-BoxUsage:c1.xlarge","USD 0.281 per Linux/UNIX (Amazon VPC), c1.xlarge instance-hour (or partial hour)","0.281","4858","1365.098"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","APS1-BoxUsage:c3.2xlarge","USD 0.226 per Linux/UNIX, c3.2xlarge instance-hour (or partial hour)","0.226","1923.6","557.719368"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","APS1-BoxUsage:c3.xlarge","$0.477 per On Demand Windows c3.xlarge Instance Hour","0.477","142.1","67.7817"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","APS1-BoxUsage:c3.xlarge","USD 0.113 per Linux/UNIX (Amazon VPC), c3.xlarge instance-hour (or partial hour)","0.113","5289.2","819.2044"],
        ["ElasticMapReduce","Amazon Elastic MapReduce","APS1-BoxUsage:m1.large","$0.044 per hour for EMR m1.large","0.044","1830.5","80.542"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","APS1-BoxUsage:m1.large","$0.233 per On Demand Linux m1.large Instance Hour","0.233","177.1","41.2643"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","APS1-BoxUsage:m1.large","$0.293 per On Demand RHEL m1.large Instance Hour","0.293","485.8","142.3394"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","APS1-BoxUsage:m1.large","$0.373 per On Demand Windows m1.large Instance Hour","0.373","485.8","181.2034"],
        ["ElasticMapReduce","Amazon Elastic MapReduce","APS1-BoxUsage:m1.medium","$0.022 per hour for EMR m1.medium","0.022","193.2","4.2504"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","APS1-BoxUsage:m1.medium","$0.117 per On Demand Linux m1.medium Instance Hour","0.117","675.5","79.0335"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","APS1-BoxUsage:m1.medium","$0.187 per On Demand Windows m1.medium Instance Hour","0.187","485.8","90.8446"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","APS1-BoxUsage:m1.xlarge","$0.467 per On Demand Linux m1.xlarge Instance Hour","0.467","177.1","82.7057"],
        ["AmazonS3","Amazon Simple Storage Service","APS1-Requests-Tier1","$0.005 per 1,000 PUT, COPY, POST, or LIST requests","0.005","2.1","0.00001"],
        ["AmazonSNS","Amazon Simple Notification Service","APS1-Requests-Tier1","First 1,000,000 Amazon SNS API Requests per month are free","0","8257.9","0"],
        ["AWSQueueService","Amazon Simple Queue Service","APS1-Requests-Tier1","First 1,000,000 Amazon SQS Requests per month are free","0","651","0"],
        ["AmazonS3","Amazon Simple Storage Service","APS1-Requests-Tier2","$0.004 per 10,000 GET and all other requests","0.004","12.6","0.000005"],
        ["AWSDataTransfer","AWS Data Transfer","APS1-SAE1-AWS-In-Bytes","$0.00 per GB - Asia Pacific (Singapore) data transfer from South America (Sao Paulo)","0","0","0"],
        ["AWSDataTransfer","AWS Data Transfer","APS1-SAE1-AWS-Out-Bytes","$0.09 per GB - Asia Pacific (Singapore) data transfer to South America (Sao Paulo)","0.09","0","0"],
        ["AmazonSimpleDB","Amazon SimpleDB","APS1-TimedStorage-ByteHrs","$0.00 per GB-Month of storage for first 1 GB-Month","0","0","0"],
        ["AmazonS3","Amazon Simple Storage Service","APS1-TimedStorage-ByteHrs","$0.0300 per GB - first 1 TB / month of storage used","0.03","0","0.000001"],
        ["AWSDataTransfer","AWS Data Transfer","APS1-UGW1-AWS-In-Bytes","$0.00 per GB - Asia Pacific (Singapore) data transfer from AWS GovCloud (US)","0","0","0"],
        ["AWSDataTransfer","AWS Data Transfer","APS1-UGW1-AWS-Out-Bytes","$0.09 per GB - Asia Pacific (Singapore) data transfer to AWS GovCloud (US)","0.09","0","0"],
        ["AmazonDynamoDB","Amazon DynamoDB","APS1-WriteCapacityUnit-Hrs","$0.00 per hour for 5 units of write capacity for a month (free tier)","0","4858","1.66796"],
        ["AWSDataTransfer","AWS Data Transfer","APS2-APN1-AWS-In-Bytes","$0.00 per GB - Asia Pacific (Sydney) data transfer from Asia Pacific (Tokyo)","0","0","0"],
        ["AWSDataTransfer","AWS Data Transfer","APS2-APS1-AWS-Out-Bytes","$0.14 per GB - Asia Pacific (Sydney) data transfer to Asia Pacific (Singapore)","0.14","0","0.000001"],
        ["AmazonWorkSpaces","Amazon WorkSpaces","APS2-AW-HW-4","$75 per month per SYD Region Performance Plus WorkSpace (Infrastructure)","75","2.8","210"],
        ["AmazonWorkSpaces","Amazon WorkSpaces","APS2-AW-SW-4","$15 per month per SYD Region Performance Plus WorkSpace (Software)","15","2.8","42"],
        ["AmazonSimpleDB","Amazon SimpleDB","APS2-BoxUsage","$0.00 per Compute-Hour consumed first 25 hours per month","0","0.1","0"],
        ["AWSDataTransfer","AWS Data Transfer","APS2-DataTransfer-In-Bytes","$0.000 per GB - data transfer in per month","0","0","0"],
        ["AWSDataTransfer","AWS Data Transfer","APS2-DataTransfer-Out-Bytes","$0.000 per GB - first 1 GB of data transferred out per month","0","0","0.000496"],
        ["AWSDataTransfer","AWS Data Transfer","APS2-DataTransfer-Regional-Bytes","$0.010 per GB - regional data transfer - in/out/between EC2 AZs or using IPs or ELB","0.01","0","0.000001"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","APS2-EBS:SnapshotUsage","$0.105 per GB-Month of snapshot data stored - Asia Pacific (Sydney)","0.105","641.2","67.326055"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","APS2-EBS:VolumeIOUsage","$0.08","0.08","1279208.7","0.102336"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","APS2-EBS:VolumeUsage","$0.08","0.08","5.2","0.41729"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","APS2-EBS:VolumeUsage.gp2","$0.12","0.12","3074.4","368.927549"],
        ["AWSDataTransfer","AWS Data Transfer","APS2-EU-AWS-In-Bytes","$0.00 per GB - Asia Pacific (Sydney) data transfer from EU (Ireland)","0","0","0"],
        ["AWSDataTransfer","AWS Data Transfer","APS2-EU-AWS-Out-Bytes","$0.14 per GB - Asia Pacific (Sydney) data transfer to EU (Ireland)","0.14","0","0.000001"],
        ["AmazonSNS","Amazon Simple Notification Service","APS2-Requests-Tier1","First 1,000,000 Amazon SNS API Requests per month are free","0","8257.9","0"],
        ["AWSQueueService","Amazon Simple Queue Service","APS2-Requests-Tier1","First 1,000,000 Amazon SQS Requests per month are free","0","651","0"],
        ["AWSDataTransfer","AWS Data Transfer","APS2-USE1-AWS-In-Bytes","$0.00 per GB - Asia Pacific (Sydney) data transfer from US East (Northern Virginia)","0","0","0"],
        ["AWSDataTransfer","AWS Data Transfer","APS2-USE1-AWS-Out-Bytes","$0.14 per GB - Asia Pacific (Sydney) data transfer to US East (Northern Virginia)","0.14","0","0.000031"],
        ["AWSDataTransfer","AWS Data Transfer","APS2-USW1-AWS-In-Bytes","$0.00 per GB - Asia Pacific (Sydney) data transfer from US West (Northern California)","0","0","0"],
        ["AWSDataTransfer","AWS Data Transfer","APS2-USW1-AWS-Out-Bytes","$0.14 per GB - Asia Pacific (Sydney) data transfer to US West (Northern California)","0.14","0","0.000001"],
        ["AWSDataTransfer","AWS Data Transfer","APS2-USW2-AWS-In-Bytes","$0.00 per GB - Asia Pacific (Sydney) data transfer from US West (Oregon)","0","0.1","0"],
        ["AWSDataTransfer","AWS Data Transfer","APS2-USW2-AWS-Out-Bytes","$0.14 per GB - Asia Pacific (Sydney) data transfer to US West (Oregon)","0.14","0.1","0.007818"],
        ["AmazonVPC","Amazon Virtual Private Cloud","APS2-VPN-Usage-Hours:ipsec.1","$0.05 per VPN Connection-Hour","0.05","485.8","24.29"],
        ["AmazonCloudFront","Amazon CloudFront","AU-DataTransfer-Out-Bytes","$0.190 per GB - first 10 TB / month data transfer out","0.19","3.7","0.701779"],
        ["AmazonCloudFront","Amazon CloudFront","AU-DataTransfer-Out-OBytes","$0.10 per GB - All data transfer out to Origin (Australia)","0.1","0","0"],
        ["AmazonCloudFront","Amazon CloudFront","AU-Requests-HTTPS-Proxy","$0.0125 per 10,000 Proxy HTTPS Requests (Australia)","0.0125","4.2","0.000006"],
        ["AmazonCloudFront","Amazon CloudFront","AU-Requests-Tier1","$0.0090 per 10,000 HTTP Requests","0.009","0.7","0.000001"],
        ["AmazonCloudFront","Amazon CloudFront","AU-Requests-Tier2-HTTPS","$0.0125 per 10,000 HTTPS Requests","0.0125","8.4","0.00001"],
        ["AmazonSimpleDB","Amazon SimpleDB","BoxUsage","$0.00 per Compute-Hour consumed first 25 hours per month","0","0.4","0"],
        ["ElasticMapReduce","Amazon Elastic MapReduce","BoxUsage","$0.011 per hour for EMR m1.small","0.011","1457.4","16.0314"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","BoxUsage","$0.075 per On Demand Windows m1.small Instance Hour","0.075","485.8","36.435"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","BoxUsage","Linux/UNIX, m1.small instance-hours used this month","0.020954378","485.8","10.179637"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","BoxUsage:c1.medium","USD 0.0486 per Linux/UNIX, c1.medium instance-hour (or partial hour)","0.0486","485.8","47.975007"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","BoxUsage:c1.xlarge","$0.650 per On Demand RHEL c1.xlarge Instance Hour","0.65","4.9","3.185"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","BoxUsage:c1.xlarge","USD 0.1944 per Linux/UNIX, c1.xlarge instance-hour (or partial hour)","0.1944","858.9","247.945476"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","BoxUsage:c1.xlarge","USD 0.4484 per Windows, c1.xlarge instance-hour (or partial hour)","0.4484","17149.3","8317.75504"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","BoxUsage:c3.2xlarge","Linux/UNIX (Amazon VPC), c3.2xlarge instance-hours used this month","0.339318597","5301.1","1798.761817"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","BoxUsage:c3.2xlarge","USD 0.40945 per Windows, c3.2xlarge instance-hour (or partial hour)","0.40945","725.9","393.133755"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","BoxUsage:c3.4xlarge","Linux/UNIX (Amazon VPC), c3.4xlarge instance-hours used this month","0.757462835","182.7","138.38846"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","BoxUsage:c3.8xlarge","Linux/UNIX (Amazon VPC), c3.8xlarge instance-hours used this month","1.300097752","3503.5","4554.892473"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","BoxUsage:c3.large","$0.188 per On Demand Windows c3.large Instance Hour","0.188","5.6","1.0528"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","BoxUsage:c3.large","Linux/UNIX (Amazon VPC), c3.large instance-hours used this month","0.104667465","298708.9","31265.10319"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","BoxUsage:c3.xlarge","$0.210 per On Demand Linux c3.xlarge Instance Hour","0.21","0.7","0.147"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","BoxUsage:hs1.8xlarge","Linux/UNIX (Amazon VPC), hs1.8xlarge instance-hours used this month","3.64597684","15386","56096.99966"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","BoxUsage:m1.large","$0.235 per On Demand RHEL m1.large Instance Hour","0.235","485.8","114.163"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","BoxUsage:m1.large","Linux/UNIX (Amazon VPC), m1.large instance-hours used this month","0.130516499","485.8","63.404915"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","BoxUsage:m1.large","USD 0.13965 per Windows, m1.large instance-hour (or partial hour)","0.13965","485.8","67.84197"],
        ["ElasticMapReduce","Amazon Elastic MapReduce","BoxUsage:m1.medium","$0.022 per hour for EMR m1.medium","0.022","48580","1068.76"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","BoxUsage:m1.medium","$0.149 per On Demand Windows m1.medium Instance Hour","0.149","56","8.344"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","BoxUsage:m1.medium","Linux/UNIX, m1.medium instance-hours used this month","0.072249776","971.6","70.197882"],
        ["ElasticMapReduce","Amazon Elastic MapReduce","BoxUsage:m1.xlarge","$0.088 per hour for EMR m1.xlarge","0.088","145740","12825.12"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","BoxUsage:m1.xlarge","Linux/UNIX (Amazon VPC), m1.xlarge instance-hours used this month","0.301299089","1457.4","439.113293"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","BoxUsage:m1.xlarge","USD 0.2793 per Windows, m1.xlarge instance-hour (or partial hour)","0.2793","961.8","445.09493"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","BoxUsage:m2.2xlarge","USD 0.1178 per Linux/UNIX (Amazon VPC), m2.2xlarge instance-hour (or partial hour)","0.1178","485.8","60.43324"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","BoxUsage:m2.4xlarge","Linux/UNIX (Amazon VPC), m2.4xlarge instance-hours used this month","0.552251573","485.8","268.283814"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","BoxUsage:m3.large","$0.140 per On Demand Linux m3.large Instance Hour","0.14","220.5","32.599"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","CW:MetricMonitorUsage","$0.50 per metric-month","0.5","4.6","2.098734"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","CW:Requests","$0.01 per 1,000 requests","0.01","32105.5","0.302929"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","DataProcessing-Bytes","$0.008 per GB Data Processed by the LoadBalancer","0.008","0.1","0.000694"],
        ["AWSDataTransfer","AWS Data Transfer","DataTransfer-In-Bytes","$0.000 per GB - data transfer in per month","0","5.7","0"],
        ["AWSDataTransfer","AWS Data Transfer","DataTransfer-Out-Bytes","$0.120 per GB - up to 10 TB / month data transfer out","0.12","68.8","8.250997"],
        ["AWSDataTransfer","AWS Data Transfer","DataTransfer-Regional-Bytes","$0.010 per GB - regional data transfer - in/out/between EC2 AZs or using IPs or ELB","0.01","0.2","0.002036"],
        ["AmazonSNS","Amazon Simple Notification Service","DeliveryAttempts-HTTP","First 100,000 Amazon SNS HTTP/HTTPS Notifications per month are free","0","41395.9","0"],
        ["AmazonSNS","Amazon Simple Notification Service","DeliveryAttempts-SMTP","First 1,000 Amazon SNS Email/Email-JSON Notifications per month are free","1.42857E-05","0.7","0.00001"],
        ["AmazonSNS","Amazon Simple Notification Service","DeliveryAttempts-SQS","There is no charge for SQS Notifications","0","5138","0"],
        ["AmazonRoute53","Amazon Route 53","DNS-Queries","$0.40 per 1,000,000 queries for the first 1 Billion queries","0.4","59.5","0.000024"],
        ["AWSSupportBusiness","AWS Support (Business)","Dollar","10% of monthly AWS usage for the first $0-$10K","0","1404.6","140.458165"],
        ["AWSSupportBusiness","AWS Support (Business)","Dollar","3% of monthly AWS usage from $250K+","250","0","0"],
        ["AWSSupportBusiness","AWS Support (Business)","Dollar","5% of monthly AWS usage from $80K-$250K","80","0","0"],
        ["AWSSupportBusiness","AWS Support (Business)","Dollar","7% of monthly AWS usage from $10K-$80K","10","0","0"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","EBS:SnapshotUsage","$0.095 per GB-Month of snapshot data stored - US East (Northern Virginia)","0.095","0.2","0.021789"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","EBS:VolumeIOUsage","$0.05 per 1 million I/O requests - US East (Northern Virginia)","0.05","6741492.8","0.337074"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","EBS:VolumeP-IOPS.piops","$0.065 per IOPS-month provisioned - US East (Northern Virginia)","0.065","2608.1","169.524194"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","EBS:VolumeUsage","$0.05 per GB-month of Magnetic provisioned storage - US East (Northern Virginia)","0.05","20.9","1.043602"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","EBS:VolumeUsage.gp2","$0.10 per GB-month of General Purpose (SSD) provisioned storage - US East (Northern Virginia)","0.1","4","0.399678"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","EBS:VolumeUsage.piops","$0.125 per GB-month of PIOPS (SSD) provisioned storage - US East (Northern Virginia)","0.125","489","61.126512"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","EBSOptimized:c1.xlarge","$0.05 for 1000 Mbps per c1.xlarge instance-hour (or partial hour)","0.05","485.8","24.29"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","EBSOptimized:c3.4xlarge","$0.10 for 2000 Mbps per c3.4xlarge instance-hour (or partial hour)","0.1","971.6","97.16"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","EBSOptimized:m1.large","$0.025 for 500 Mbps per m1.large instance-hour (or partial hour)","0.025","1457.4","36.435"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","EBSOptimized:m1.xlarge","$0.05 for 1000 Mbps per m1.xlarge instance-hour (or partial hour)","0.05","1854.3","92.715"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","EBSOptimized:m2.2xlarge","$0.025 for 500 Mbps per m2.2xlarge instance-hour (or partial hour)","0.025","485.8","12.824"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","EBSOptimized:m3.2xlarge","$0.05 for 1000 Mbps per m3.2xlarge instance-hour (or partial hour)","0.05","2429","121.45"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","ElasticIP:IdleAddress","$0.005 per Elastic IP address not attached to a running instance per hour (prorated)","0.005","968.8","4.843924"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","ElasticIP:Remap","$0.10 per Elastic IP address remap - additional remap / month over 100","0.1","0.7","0.058487"],
        ["AWSDirectConnect","AWS Direct Connect","EqDC2-DataXfer-Out-Bytes:dc.1","$0.020 per GB - Amazon VPC to AWS Direct Connect data transfer OUT per month (US East to Equinix DC2)","0.02","0","0.000101"],
        ["AWSDataTransfer","AWS Data Transfer","EU-APN1-AWS-In-Bytes","$0.00 per GB - EU (Ireland) data transfer from Asia Pacific (Tokyo)","0","0","0"],
        ["AWSDataTransfer","AWS Data Transfer","EU-APN1-AWS-Out-Bytes","$0.02 per GB - EU (Ireland) data transfer to Asia Pacific (Tokyo)","0.02","0","0"],
        ["AWSDataTransfer","AWS Data Transfer","EU-APS1-AWS-In-Bytes","$0.00 per GB - EU (Ireland) data transfer from Asia Pacific (Singapore)","0","0","0"],
        ["AWSDataTransfer","AWS Data Transfer","EU-APS1-AWS-Out-Bytes","$0.02 per GB - EU (Ireland) data transfer to Asia Pacific (Singapore)","0.02","0","0"],
        ["AWSDataTransfer","AWS Data Transfer","EU-APS2-AWS-In-Bytes","$0.00 per GB - EU (Ireland) data transfer from Asia Pacific (Sydney)","0","0","0"],
        ["AWSDataTransfer","AWS Data Transfer","EU-APS2-AWS-Out-Bytes","$0.02 per GB - EU (Ireland) data transfer to Asia Pacific (Sydney)","0.02","0","0"],
        ["AmazonSimpleDB","Amazon SimpleDB","EU-BoxUsage","$0.00 per Compute-Hour consumed first 25 hours per month","0","0.1","0"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","EU-BoxUsage:c1.xlarge","USD 0.288 per Linux/UNIX, c1.xlarge instance-hour (or partial hour)","0.288","11.9","3.470972"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","EU-BoxUsage:c3.2xlarge","USD 0.298 per Linux/UNIX, c3.2xlarge instance-hour (or partial hour)","0.298","1225.7","376.817894"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","EU-BoxUsage:m1.medium","$0.095 per On Demand Linux m1.medium Instance Hour","0.095","7.7","0.7315"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","EU-BoxUsage:m1.medium","$0.149 per On Demand Windows m1.medium Instance Hour","0.149","485.8","72.3842"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","EU-BoxUsage:m3.2xlarge","$0.616 per On Demand Linux m3.2xlarge Instance Hour","0.616","798","491.568"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","EU-BoxUsage:m3.large","$0.154 per On Demand Linux m3.large Instance Hour","0.154","38.5","5.929"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","EU-BoxUsage:m3.medium","$0.133 per On Demand Windows m3.medium Instance Hour","0.133","485.8","64.6114"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","EU-BoxUsage:t1.micro","$0.020 per On Demand Linux t1.micro Instance Hour","0.02","485.8","9.716"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","EU-BoxUsage:t1.micro","$0.020 per On Demand Windows t1.micro Instance Hour","0.02","485.8","9.716"],
        ["AWSDataTransfer","AWS Data Transfer","EU-CloudFront-In-Bytes","$0.00 per GB data transfer in to EU (Ireland) from CloudFront","0","0","0"],
        ["AWSDataTransfer","AWS Data Transfer","EU-CloudFront-Out-Bytes","$0.02 per GB data transfer out of EU (Ireland) to CloudFront","0.02","0","0.000001"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","EU-CW:Requests","$0.01 per 1,000 requests","0.01","8026.2","0.080262"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","HeavyUsage:m2.4xlarge","USD 0.1908 hourly fee per Linux/UNIX (Amazon VPC), m2.4xlarge instance","0.1908","2083.2","397.47456"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","HeavyUsage:m2.4xlarge","USD 0.24480000000000002 hourly fee per Linux/UNIX, m2.4xlarge instance","0.2448","520.8","127.49184"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","HeavyUsage:m2.xlarge","USD 0.061200000000000004 hourly fee per Linux/UNIX, m2.xlarge instance","0.0612","5728.8","350.60256"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","HeavyUsage:m3.2xlarge","USD 0.1881 hourly fee per Linux/UNIX, m3.2xlarge instance","0.1881","2083.2","391.84992"],
        ["AmazonRoute53","Amazon Route 53","HostedZone","$0.50 per Hosted Zone for the first 25 Hosted Zones","0.5","0.7","0.35"],
        ["AmazonCloudFront","Amazon CloudFront","IN-DataTransfer-Out-Bytes","$0.170 per GB - first 10 TB / month data transfer out (India)","0.17","0","0.008076"],
        ["AmazonCloudFront","Amazon CloudFront","IN-DataTransfer-Out-OBytes","$0.16 per GB - All data transfer out to Origin (India)","0.16","0","0"],
        ["AmazonCloudFront","Amazon CloudFront","IN-Requests-HTTPS-Proxy","$0.0120 per 10,000 Proxy HTTPS Requests (India)","0.012","2.8","0.000003"],
        ["AmazonCloudFront","Amazon CloudFront","IN-Requests-Tier1","$0.0090 per 10,000 HTTP Requests (India)","0.009","3.5","0.000003"],
        ["AmazonCloudFront","Amazon CloudFront","IN-Requests-Tier2-HTTPS","$0.0120 per 10,000 HTTPS Requests (India)","0.012","1.4","0.000001"],
        ["AmazonRDS","Amazon RDS Service","InstanceUsage:db.t1.micro","$0.025 per RDS Micro Instance hour (or partial hour)","0.025","485.8","12.145"],
        ["AmazonRoute53","Amazon Route 53","Intra-AWS-DNS-Queries","Queries to Alias records are free of charge","0","29.4","0"],
        ["AmazonCloudFront","Amazon CloudFront","Invalidations","$0.000 per URL - first 1,000 URLs / month.","0","11.9","0"],
        ["AmazonCloudFront","Amazon CloudFront","JP-DataTransfer-Out-Bytes","$0.190 per GB - first 10 TB / month data transfer out","0.19","0.1","0.011042"],
        ["AmazonCloudFront","Amazon CloudFront","JP-DataTransfer-Out-OBytes","$0.060 per GB - All data transfer out to Origin (Japan)","0.06","0","0.000001"],
        ["AmazonCloudFront","Amazon CloudFront","JP-Requests-HTTPS-Proxy","$0.0120 per 10,000 Proxy HTTPS Requests (Japan)","0.012","192.5","0.000231"],
        ["AmazonCloudFront","Amazon CloudFront","JP-Requests-Tier1","$0.0090 per 10,000 HTTP Requests","0.009","704.2","0.000633"],
        ["AmazonCloudFront","Amazon CloudFront","JP-Requests-Tier2-HTTPS","$0.012 per 10,000 HTTPS Requests","0.012","6.3","0.000008"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","LoadBalancerUsage","$0.025 per LoadBalancer-hour (or partial hour)","0.025","153.3","3.8325"],
        ["AmazonRDS","Amazon RDS Service","Multi-AZUsage:db.m1.small","$0.11 per RDS Small, Multi-AZ Instance hour (or partial hour) running MySQL - BYOL","0.11","485.8","53.438"],
        ["AmazonRDS","Amazon RDS Service","RDS:Multi-AZ-StorageUsage","$0.20 per GB-month of provisioned storage for Multi-AZ deployments","0.2","3.3","0.652957"],
        ["AmazonRDS","Amazon RDS Service","RDS:StorageIOUsage","$0.10","0.1","638401.4","0.06384"],
        ["AmazonRDS","Amazon RDS Service","RDS:StorageUsage","$0.10 per GB-month of provisioned storage","0.1","3.9","0.391775"],
        ["AmazonDynamoDB","Amazon DynamoDB","ReadCapacityUnit-Hrs","$0.00 per hour for 10 units of read capacity for a month (free tier)","0","4858","0"],
        ["AmazonSES","Amazon Simple Email Service","Recipients-EC2","Cost per recipient of SendEmail or SendRawEmail EC2 USE1","0","6.3","0"],
        ["AWSQueueService","Amazon Simple Queue Service","Requests-RBP","First 1,000,000 Amazon SQS Requests per month are free","1.8657E-07","11502.4","0.002146"],
        ["AmazonS3","Amazon Simple Storage Service","Requests-Tier1","$0.005 per 1,000 PUT, COPY, POST, or LIST requests","0.005","154.7","0.000773"],
        ["AmazonSNS","Amazon Simple Notification Service","Requests-Tier1","First 1,000,000 Amazon SNS API Requests per month are free","0","0.7","0"],
        ["AmazonS3","Amazon Simple Storage Service","Requests-Tier2","$0.004 per 10,000 GET and all other requests","0.004","1377.6","0.000551"],
        ["AmazonS3","Amazon Simple Storage Service","Requests-Tier3","$0.050 per 1,000 Glacier Requests (US)","0.05","20.3","0.001015"],
        ["AmazonCloudFront","Amazon CloudFront","SA-DataTransfer-Out-Bytes","$0.250 per GB - first 10 TB / month data transfer out","0.25","1","0.241218"],
        ["AmazonCloudFront","Amazon CloudFront","SA-Requests-Tier1","$0.0160 per 10,000 HTTP Requests","0.016","7","0.000011"],
        ["AmazonCloudFront","Amazon CloudFront","SA-Requests-Tier2-HTTPS","$0.0220 per 10,000 HTTPS Requests","0.022","7","0.000015"],
        ["AWSDataTransfer","AWS Data Transfer","SAE1-APN1-AWS-In-Bytes","$0.00 per GB - South America (Sao Paulo) data transfer from Asia Pacific (Tokyo)","0","0","0"],
        ["AWSDataTransfer","AWS Data Transfer","SAE1-APN1-AWS-Out-Bytes","$0.16 per GB - South America (Sao Paulo) data transfer to Asia Pacific (Tokyo)","0.16","0","0"],
        ["AWSDataTransfer","AWS Data Transfer","SAE1-APS1-AWS-In-Bytes","$0.00 per GB - South America (Sao Paulo) data transfer from Asia Pacific (Singapore)","0","0","0"],
        ["AWSDataTransfer","AWS Data Transfer","SAE1-APS1-AWS-Out-Bytes","$0.16 per GB - South America (Sao Paulo) data transfer to Asia Pacific (Singapore)","0.16","0","0"],
        ["AWSDataTransfer","AWS Data Transfer","SAE1-APS2-AWS-In-Bytes","$0.00 per GB - South America (Sao Paulo) data transfer from Asia Pacific (Sydney)","0","0","0"],
        ["AWSDataTransfer","AWS Data Transfer","SAE1-APS2-AWS-Out-Bytes","$0.16 per GB - South America (Sao Paulo) data transfer to Asia Pacific (Sydney)","0.16","0","0"],
        ["AmazonSimpleDB","Amazon SimpleDB","SAE1-BoxUsage","$0.00 per Compute-Hour consumed first 25 hours per month","0","0.1","0"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","SAE1-BoxUsage:t1.micro","$0.027 per On Demand Linux t1.micro Instance Hour","0.027","485.8","13.1166"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","SAE1-CW:Requests","$0.00 per request - first 1,000,000 requests","0","8026.9","0"],
        ["AWSDataTransfer","AWS Data Transfer","SAE1-DataTransfer-In-Bytes","$0.000 per GB - data transfer in per month","0","0","0"],
        ["AWSDataTransfer","AWS Data Transfer","SAE1-DataTransfer-Out-Bytes","$0.000 per GB - first 1 GB of data transferred out per month","0","0","0"],
        ["AWSDataTransfer","AWS Data Transfer","SAE1-DataTransfer-Regional-Bytes","$0.010 per GB - regional data transfer - in/out/between EC2 AZs or using elastic IPs or ELB","0.01","0","0"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","SAE1-EBS:SnapshotUsage","$0.13 per GB-Month of snapshot data stored - South America (Sao Paulo)","0.13","333.2","43.314267"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","SAE1-EBS:VolumeIOUsage","$0.12 per 1 million I/O requests - South America (Sao Paulo)","0.12","380852.5","0.045702"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","SAE1-EBS:VolumeUsage","$0.12 per GB-month of Magnetic provisioned storage - South America (Sao Paulo)","0.12","5.2","0.625936"],
        ["AWSDataTransfer","AWS Data Transfer","SAE1-EU-AWS-In-Bytes","$0.00 per GB - South America (Sao Paulo) data transfer from EU (Ireland)","0","0","0"],
        ["AWSDataTransfer","AWS Data Transfer","SAE1-EU-AWS-Out-Bytes","$0.16 per GB - South America (Sao Paulo) data transfer to EU (Ireland)","0.16","0","0"],
        ["AmazonSNS","Amazon Simple Notification Service","SAE1-Requests-Tier1","First 1,000,000 Amazon SNS API Requests per month are free","0","8257.9","0"],
        ["AWSQueueService","Amazon Simple Queue Service","SAE1-Requests-Tier1","First 1,000,000 Amazon SQS Requests per month are free","0","651","0"],
        ["AWSDataTransfer","AWS Data Transfer","SAE1-USE1-AWS-In-Bytes","$0.00 per GB - South America (Sao Paulo) data transfer from US East (Northern Virginia)","0","0","0"],
        ["AWSDataTransfer","AWS Data Transfer","USW2-APS1-AWS-In-Bytes","$0.00 per GB - US West (Oregon) data transfer from Asia Pacific (Singapore)","0","0","0"],
        ["AWSDataTransfer","AWS Data Transfer","USW2-APS1-AWS-Out-Bytes","$0.02 per GB - US West (Oregon) data transfer to Asia Pacific (Singapore)","0.02","0","0.000001"],
        ["AWSDataTransfer","AWS Data Transfer","USW2-APS2-AWS-In-Bytes","$0.00 per GB - US West (Oregon) data transfer from Asia Pacific (Sydney)","0","0","0"],
        ["AWSDataTransfer","AWS Data Transfer","USW2-APS2-AWS-Out-Bytes","$0.02 per GB - US West (Oregon) data transfer to Asia Pacific (Sydney)","0.02","0","0.000001"],
        ["AmazonSES","Amazon Simple Email Service","USW2-AttachmentsSize-Bytes","Cost per GB of attachments USW2","0","0","0.000007"],
        ["AmazonSimpleDB","Amazon SimpleDB","USW2-BoxUsage","$0.00 per Compute-Hour consumed first 25 hours per month","0","0","0"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","USW2-BoxUsage","$0.044 per On Demand Linux m1.small Instance Hour","0.044","9018.8","396.8272"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","USW2-BoxUsage:c1.xlarge","$0.520 per On Demand Linux c1.xlarge Instance Hour","0.52","1302.7","677.404"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","USW2-BoxUsage:c1.xlarge","$0.650 per On Demand RHEL c1.xlarge Instance Hour","0.65","485.8","315.77"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","USW2-BoxUsage:c3.2xlarge","$0.550 per On Demand RHEL c3.2xlarge Instance Hour","0.55","720.3","396.165"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","USW2-BoxUsage:c3.2xlarge","USD 0.224 per Linux/UNIX, c3.2xlarge instance-hour (or partial hour)","0.224","485.8","140.660913"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","USW2-BoxUsage:c3.2xlarge","USD 0.431 per Windows, c3.2xlarge instance-hour (or partial hour)","0.431","285.6","138.713503"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","USW2-BoxUsage:c3.4xlarge","$0.840 per On Demand Linux c3.4xlarge Instance Hour","0.84","21.7","18.228"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","USW2-BoxUsage:c3.8xlarge","$1.680 per On Demand Linux c3.8xlarge Instance Hour","1.68","935.9","1572.312"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","USW2-BoxUsage:c3.large","$0.105 per On Demand Linux c3.large Instance Hour","0.105","2438.8","256.074"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","USW2-BoxUsage:c3.large","$0.165 per On Demand RHEL c3.large Instance Hour","0.165","0.7","0.1155"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","USW2-BoxUsage:c3.xlarge","$0.210 per On Demand Linux c3.xlarge Instance Hour","0.21","485.8","102.018"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","USW2-BoxUsage:m3.2xlarge","$0.560 per On Demand Linux m3.2xlarge Instance Hour","0.56","505.4","283.024"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","USW2-BoxUsage:m3.2xlarge","$0.690 per On Demand RHEL m3.2xlarge Instance Hour","0.69","971.6","670.404"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","USW2-BoxUsage:m3.large","$0.140 per On Demand Linux m3.large Instance Hour","0.14","30.1","4.214"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","USW2-BoxUsage:m3.large","$0.200 per On Demand RHEL m3.large Instance Hour","0.2","1686.3","337.26"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","USW2-BoxUsage:m3.medium","$0.070 per On Demand Linux m3.medium Instance Hour","0.07","369.6","25.872"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","USW2-BoxUsage:m3.medium","$0.130 per On Demand RHEL m3.medium Instance Hour","0.13","1943.2","252.616"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","USW2-BoxUsage:m3.xlarge","$0.280 per On Demand Linux m3.xlarge Instance Hour","0.28","454.3","127.204"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","USW2-BoxUsage:m3.xlarge","$0.340 per On Demand RHEL m3.xlarge Instance Hour","0.34","497.7","169.218"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","USW2-BoxUsage:m3.xlarge","$0.532 per On Demand Windows m3.xlarge Instance Hour","0.532","485.8","258.4456"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","USW2-BoxUsage:t1.micro","$0.020 per On Demand Linux t1.micro Instance Hour","0.02","973","19.46"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","USW2-BoxUsage:t1.micro","$0.020 per On Demand Windows t1.micro Instance Hour","0.02","424.2","8.484"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","USW2-BoxUsage:t2.small","$0.026 per On Demand Linux t2.small Instance Hour","0.026","0.7","0.0182"],
        ["AWSDataTransfer","AWS Data Transfer","USW2-CloudFront-In-Bytes","$0.00 per GB data transfer in to US West (Oregon) from CloudFront","0","0","0"],
        ["AWSDataTransfer","AWS Data Transfer","USW2-CloudFront-Out-Bytes","$0.02 per GB data transfer out of US West (Oregon) to CloudFront","0.02","59","1.17953"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","USW2-CW:AlarmMonitorUsage","$0.10 per alarm-month","0.1","0.6","0.064985"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","USW2-CW:MetricMonitorUsage","$0.50 per metric-month","0.5","4.7","2.37379"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","USW2-CW:Requests","$0.01 per 1,000 requests","0.01","126886.2","1.268862"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","USW2-DataProcessing-Bytes","$0.008 per GB Data Processed by the LoadBalancer","0.008","0.7","0.005658"],
        ["AWSDataTransfer","AWS Data Transfer","USW2-DataTransfer-In-Bytes","$0.000 per GB - data transfer in per month","0","378.9","0"],
        ["AWSDataTransfer","AWS Data Transfer","USW2-DataTransfer-Out-Bytes","$0.120 per GB - up to 10 TB / month data transfer out","0.12","49.6","5.936449"],
        ["AWSDataTransfer","AWS Data Transfer","USW2-DataTransfer-Regional-Bytes","$0.010 per GB - regional data transfer - in/out/between EC2 AZs or using IPs or ELB","0.01","491.6","4.9158"],
        ["AmazonSNS","Amazon Simple Notification Service","USW2-DeliveryAttempts-SMTP","First 1,000 Amazon SNS Email/Email-JSON Notifications per month are free","0","88.9","0"],
        ["AmazonSNS","Amazon Simple Notification Service","USW2-DeliveryAttempts-SQS","There is no charge for SQS Notifications","0","5061.7","0"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","USW2-EBS:SnapshotUsage","$0.095 per GB-Month of snapshot data stored - US West (Oregon)","0.095","6","0.566261"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","USW2-EBS:VolumeIOUsage","$0.05 per 1 million I/O requests - US West (Oregon)","0.05","67827615.8","3.391381"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","USW2-EBS:VolumeP-IOPS.piops","$0.065 per IOPS-month provisioned - US West (Oregon)","0.065","4955.3","322.095968"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","USW2-EBS:VolumeUsage","$0.05 per GB-month of Magnetic provisioned storage - US West (Oregon)","0.05","13","0.651076"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","USW2-EBS:VolumeUsage.gp2","$0.10 per GB-month of General Purpose (SSD) provisioned storage - US West (Oregon)","0.1","39.1","3.913414"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","USW2-EBS:VolumeUsage.piops","$0.125 per GB-month of PIOPS (SSD) provisioned storage - US West (Oregon)","0.125","2180.3","272.542742"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","USW2-EBSOptimized:c1.xlarge","$0.05 for 1000 Mbps per c1.xlarge instance-hour (or partial hour)","0.05","485.8","24.29"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","USW2-EBSOptimized:c3.4xlarge","$0.10 for 2000 Mbps per c3.4xlarge instance-hour (or partial hour)","0.1","2.8","0.28"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","USW2-ElasticIP:IdleAddress","$0.005 per Elastic IP address not attached to a running instance per hour (prorated)","0.005","971.6","4.85782"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","USW2-ElasticIP:Remap","$0.00 per Elastic IP address remap - first 100 remaps / month","0","2.8","0"],
        ["AWSDataTransfer","AWS Data Transfer","USW2-EU-AWS-In-Bytes","$0.00 per GB - US West (Oregon) data transfer from EU (Ireland)","0","0","0"],
        ["AWSDataTransfer","AWS Data Transfer","USW2-EU-AWS-Out-Bytes","$0.02 per GB - US West (Oregon) data transfer to EU (Ireland)","0.02","0","0.000001"],
        ["AmazonRDS","Amazon RDS Service","USW2-InstanceUsage:db.m1.small","$0.06 per RDS Small Instance hour (or partial hour) running PostgreSQL","0.06","971.6","58.296"],
        ["AmazonRDS","Amazon RDS Service","USW2-InstanceUsage:db.t1.micro","$0.025 per RDS Micro Instance hour (or partial hour)","0.025","485.8","12.145"],
        ["AmazonEC2","Amazon Elastic Compute Cloud","USW2-LoadBalancerUsage","$0.025 per LoadBalancer-hour (or partial hour)","0.025","3263.4","81.585"],
        ["AmazonRDS","Amazon RDS Service","USW2-Multi-AZUsage:db.m3.large","$0.37 per RDS Second Gen Large, Multi-AZ Instance hour (or partial hour) running MySQL - BYOL","0.37","485.8","179.746"],
        ["AmazonRDS","Amazon RDS Service","USW2-Multi-AZUsage:db.m3.xlarge","$0.74 per RDS Second Gen Extra Large, Multi-AZ Instance hour (or partial hour) running MySQL - BYOL","0.74","485.8","359.492"],
        ["AmazonElastiCache","Amazon ElastiCache","USW2-NodeUsage:cache.m1.large","$0.226","0.226","485.8","109.7908"],
        ["AmazonElastiCache","Amazon ElastiCache","USW2-NodeUsage:cache.t1.micro","$0.000 per Micro Cache node-hour (or partial hour) running Memcached under monthly Free Tier","0","971.6","9.8252"],
        ["AmazonRDS","Amazon RDS Service","USW2-RDS:Multi-AZ-PIOPS","$0.20 per IOPS-month of Multi-AZ Provisioned IOPS","0.2","653","130.591398"],
        ["AmazonRDS","Amazon RDS Service","USW2-RDS:Multi-AZ-PIOPS-Storage","$0.25 per GB-month of Multi-AZ Provisioned IOPS Storage","0.25","65.3","16.323924"],
        ["AmazonRDS","Amazon RDS Service","USW2-RDS:Multi-AZ-StorageUsage","$0.20 per GB-month of provisioned storage for Multi-AZ deployments","0.2","65.3","13.05914"],
        ["AmazonRDS","Amazon RDS Service","USW2-RDS:StorageIOUsage","$0.10","0.1","32338841.5","3.233884"],
        ["AmazonRDS","Amazon RDS Service","USW2-RDS:StorageUsage","$0.10 per GB-month of provisioned storage","0.1","3.3","0.326479"],
        ["AmazonSES","Amazon Simple Email Service","USW2-Recipients","Cost per recipient of SendEmail or SendRawEmail USW2","0.0001","2.8","0.00028"],
        ["AmazonSES","Amazon Simple Email Service","USW2-Recipients-EC2","Cost per recipient of SendEmail or SendRawEmail EC2 USW2","0","203.7","0"],
        ["AmazonDynamoDB","Amazon DynamoDB","WriteCapacityUnit-Hrs","$0.00 per hour for 5 units of write capacity for a month (free tier)","0","4858","1.4651"],
        ["AmazonZocalo","Amazon Zocalo","Zocalo-USE1-InclStorageByteHrs","$0.00 per GB / month of included storage used in the USE1 region","0","0","0"],
        ["AmazonZocalo","Amazon Zocalo","Zocalo-USE1-WSOnly-UserHrs","$0 per WorkSpaces Only user per month in the USE1 region","0","0.6","0"]
    ]


    rex_start_date = re.compile(r'#START_YMD#')
    rex_end_date = re.compile(r'#END_YMD#')
    rex_s3key = re.compile(r'#NOW#')
    rex_linked_account_id = re.compile(r'#LINKED_ACCOUNT_ID#')
    rex_linked_account_name = re.compile(r'#LINKED_ACCOUNT_NAME#')

    rexs = [
        re.compile(r'#PRODUCT_CODE#'),
        re.compile(r'#PRODUCT_NAME#'),
        re.compile(r'#USAGE_TYPE#'),
        re.compile(r'#ITEM_DESCRIPTION#'),
        re.compile(r'#QUANTITY#'),
        re.compile(r'#COST#'),
        re.compile(r'#AZ#')
    ]

    MONTHLY_VAR = 1
    ITEM_VAR = 1

    def _get_monthly_random(self, month_date):
        now_month =month_date.month * 100

        random.seed(now_month)
        r = 1 - self.MONTHLY_VAR*0.5 + random.random()*self.MONTHLY_VAR

        return r

    def _get_item_random(self, account_i, item_i, month_date):
        random.seed(month_date.month*100 + account_i * 500 + item_i)
        r = 1 - self.ITEM_VAR*0.5 + random.random()*self.ITEM_VAR

        return r * self._get_monthly_random(month_date)

    def __init__(self, sample):
        OutputPlugin.__init__(self, sample)

    def _build_common_msg(self, msg, start_ymd, end_ymd, last_modified):
        msg = self.rex_start_date.sub(start_ymd, msg)
        msg = self.rex_end_date.sub(end_ymd, msg)
        msg = self.rex_s3key.sub(last_modified, msg)

        return msg

    def _build_common_total_msg(self, msg, start_ymd, end_ymd, last_modified, invoice_id, payer_id):
        msg = self._build_common_msg(msg, start_ymd, end_ymd, last_modified)
        msg = re.sub(r'#INVOICE_ID#', invoice_id, msg)
        msg = re.sub(r'#PAYER_ID#', payer_id, msg)

        return msg

    def generate_billing(self, template_msg, month):
        msg = template_msg['_raw']
        out = ''


        month_date = billing_utils.get_month_day(month)
        month_days = calendar.monthrange(month_date.year, month_date.month)[1]
        end_date = month_date + datetime.timedelta(days=month_days) - datetime.timedelta(microseconds=1)
        start_ymd = month_date.strftime('%Y/%m/%d')
        end_ymd = month_date.strftime('%Y/%m/') + str(month_days)
        last_modified = end_date.strftime("%Y-%m-%dT%H:%M:%S") + '.000Z'
        invoice_id = re.search(r'(?<=InvoiceID=)[^,]+', msg).group(0)
        payer_id = re.search(r'(?<=PayerAccountId=)[^,]+', msg).group(0)


        base_msg = self._build_common_msg(msg, start_ymd, end_ymd, last_modified)
        base_account_total_msg = self._build_common_total_msg(self.sample_account_total, start_ymd, end_ymd, last_modified, invoice_id, payer_id)
        base_statement_total_msg = self._build_common_total_msg(self.sample_statement_total, start_ymd, end_ymd, last_modified, invoice_id, payer_id)

        statement_total = 0
        for account_index, account in enumerate(billing_fixture.LINKED_ACCOUNTS):
            account_total = 0

            base_msg_account = base_msg
            base_msg_account = self.rex_linked_account_id.sub(account['id'], base_msg_account)
            base_msg_account = self.rex_linked_account_name.sub(account['name'], base_msg_account)


            for item_i, item in enumerate(self.sample_billing_items):
                r = self._get_item_random(account_index, item_i, month_date)
                price = r * r * 600
                msg_line = base_msg_account
                msg_line = self.rexs[0].sub(item[0], msg_line)                   # ProductCode
                msg_line = self.rexs[1].sub(item[1], msg_line)                   # ProductName
                msg_line = self.rexs[2].sub(item[2], msg_line)                   # UsageType
                msg_line = self.rexs[3].sub(item[3], msg_line)                   # ItemDescription
                msg_line = self.rexs[4].sub(str(float(item[5])*r), msg_line)     # UsageQuantity
                msg_line = self.rexs[5].sub(str(price), msg_line)     # TotalCost
                msg_line = self.rexs[6].sub(billing_fixture.AZ_LIST[(int(r*1000))%len(billing_fixture.AZ_LIST)], msg_line)     # AZ

                random.seed(account_index)
                for _ in range(int(random.random() * 10)):
                    # statistic
                    account_total += float(price)*r
                    statement_total += float(price)*r

                    # push
                    out += billing_utils.build_event(end_date, month_date, template_msg, msg_line, False)


                # account total
            account_total_msg = base_account_total_msg
            account_total_msg = self.rex_linked_account_id.sub(account["id"], account_total_msg)
            account_total_msg = self.rex_linked_account_name.sub(account["name"], account_total_msg)
            account_total_msg = re.sub(r'#COST#', str(account_total), account_total_msg)

            out += billing_utils.build_event(end_date, month_date, template_msg, account_total_msg, False)

        # statement total
        statement_total_msg = base_statement_total_msg
        statement_total_msg = re.sub(r'#COST#', str(statement_total), statement_total_msg)

        out += billing_utils.build_event(end_date, month_date, template_msg, statement_total_msg, False)

        return out

if __name__ == "__main__":
    monthly_billing = BaseMonthlyBilling(object)
    m = {
        'index': 'hello',
        'sourcetype': 'b',
        'host': '1',
        '_raw': 'InvoiceID=#INVOICE_ID#, PayerAccountId=#PAYER_ID#, LinkedAccountId=#LINKED_ACCOUNT_ID#, RecordType=LinkedLineItem, RecordId=#RECORD_ID#, ProductName=#PRODUCT_NAME#, RateId=#RATE_ID#, SubscriptionId=#SUBSCRIPTION_ID#, PricingPlanId=#PLAN_ID#, UsageType=#USAGE_TYPE#, Operation=#OPERATION#, AvailabilityZone=#AZ#, ReservedInstance=#RESERVED_INSTANCE#, ItemDescription=#ITEM_DESCRIPTION#, UsageStartDate=#START_YMD#, UsageEndDate=#END_YMD#, UsageQuantity=#QUANTITY#, BlendedCost=#BLENDED_COST#, ResourceId=#RESOURCE_ID#, user:Name=#TAG_NAME#, user:env=#TAG_ENV#, S3KeyLastModified="#NOW#"'
    }
    # monthly_billing.generate_billing(m, 2)
    monthly_billing.generate_billing(m, 1)