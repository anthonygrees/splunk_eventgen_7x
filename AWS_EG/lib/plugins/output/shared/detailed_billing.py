from __future__ import division
import datetime
import time
import re
import random
import calendar
import shared.billing_utils as billing_utils
import shared.billing_fixture as billing_fixture
from outputplugin import OutputPlugin


class BaseDetailedBilling(OutputPlugin):
    name = 'aws_billing_detailed_base'
    MAXQUEUELENGTH = 10

    sample_statement_total = 'InvoiceID=, PayerAccountId=#PAYER_ID#, LinkedAccountId=, RecordType=StatementTotal, RecordId=, ProductName=, RateId=, SubscriptionId=, PricingPlanId=, UsageType=, Operation=, AvailabilityZone=, ReservedInstance=, ItemDescription=Total statement amount for period XXXX-XX-01 00:00:00 - XXXX-XX-XX 23:59:59, UsageStartDate=, UsageEndDate=, UsageQuantity=, BlendedRate=, BlendedCost=#BLENDED_COST#, UnBlendedRate=, UnBlendedCost=#BLENDED_COST#, ResourceId=, S3KeyLastModified=#NOW#'

    # list of billing items and sample cost
    sample_billing_items = [
        #"ProductName","Operation","UsageType"
        ['AWS Key Management Service', 'Decrypt', 'us-east-1-KMS-Requests'],
        ['Amazon DynamoDB', 'BatchWriteItem', 'DataTransfer-In-Bytes'],
        ['Amazon Glacier', 'ListVaults', 'APN1-USE1-AWS-Out-Bytes'],
        ['Amazon RDS Service', 'CreateDBInstance', 'APS1-RDS:Multi-AZ-GP2-Storage'],
        ['Amazon Route 53', 'A', 'DNS-Queries'],
        ['Amazon Simple Notification Service', 'CreateTopic', 'Requests-Tier1'],
        ['Amazon Simple Queue Service', 'ChgVis', 'Requests-RBP'],
        ['Amazon Simple Storage Service', 'CompleteMultipartUpload', 'Requests-Tier1'],
        ['Amazon SimpleDB', 'StandardStorage', 'TimedStorage-ByteHrs'],
        ['Amazon Virtual Private Cloud', 'CreateVpnConnection', 'APN1-DataTransfer-In-Bytes'],
        ['AmazonCloudWatch', 'HourlyStorageMetering', 'TimedStorage-ByteHrs']
    ]

    rex_start_date = re.compile(r'#START_YMD#')
    rex_end_date = re.compile(r'#END_YMD#')
    rex_payer_id = re.compile(r'#PAYER_ID#')
    rex_linked_account_id = re.compile(r'#LINKED_ACCOUNT_ID#')
    rex_s3key = re.compile(r'#NOW#')

    rex_product_name = re.compile(r'#PRODUCT_NAME#')
    rex_operation = re.compile(r'#OPERATION#')
    rex_usage = re.compile(r'#USAGE_TYPE#')
    rex_az = re.compile(r'#AZ#')
    rex_cost = re.compile(r'#BLENDED_COST#')
    rex_ri = re.compile(r'#RESERVED_INSTANCE#')
    rex_quantity = re.compile(r'#QUANTITY#')
    rex_id = re.compile(r'#RESOURCE_ID#')
    rex_tag_name = re.compile(r'#TAG_NAME#')
    rex_tag_env = re.compile(r'#TAG_ENV#')
    rex_desc = re.compile(r'#ITEM_DESCRIPTION#')

    MONTHLY_VAR = 1
    ITEM_VAR = 1

    # will generate a random number between [0,1]+0.5, using current time as the random seed
    def _get_monthly_random(self):
        now = datetime.datetime.now()
        now_month = now.year*100 + now.month

        random.seed(now_month)
        r = 1 - self.MONTHLY_VAR*0.5 + random.random()*self.MONTHLY_VAR

        return r

    def _get_item_random(self, account_index, item_index, day=0):
        now = datetime.datetime.now()
        now_month = now.year*10000 + now.month*100

        random.seed(now_month + account_index + item_index + day)
        r = 1 - self.ITEM_VAR*0.5 + random.random()*self.ITEM_VAR

        return r * self._get_monthly_random()

    def _build_msg(self, az, msg, r, start_date, end_date, product_name, operation, usage, ri, cost, quantity, desc = None):
        if not quantity:
            quantity = str(round(r,8))
        if not cost:
            cost = str(round(r*10,8))

        msg = self.rex_start_date.sub(start_date.strftime("%Y-%m-%d %H:%M:%S"), msg)
        msg = self.rex_end_date.sub(end_date.strftime("%Y-%m-%d %H:%M:%S"), msg)
        msg = self.rex_product_name.sub(product_name, msg)
        msg = self.rex_operation.sub(operation, msg)
        msg = self.rex_usage.sub(usage, msg)
        msg = self.rex_az.sub(az, msg)
        msg = self.rex_cost.sub(cost, msg)
        msg = self.rex_ri.sub(ri, msg)
        # msg = self.rex_id.sub('N/A', msg)b
        msg = self.rex_tag_name.sub(billing_fixture.TAG_NAME_LIST[(int(r*1000))%len(billing_fixture.TAG_NAME_LIST)], msg)
        msg = self.rex_tag_env.sub(billing_fixture.TAG_ENV_LIST[(int(r*1000))%len(billing_fixture.TAG_ENV_LIST)], msg)
        msg = self.rex_quantity.sub(quantity, msg)
        if desc:
            msg = self.rex_desc.sub(desc, msg)

        return msg

    def __init__(self, sample):
        OutputPlugin.__init__(self, sample)

    def generate_billing(self, template_msg, month):
        msg = template_msg['_raw']
        out = ''

        month_date = billing_utils.get_month_day(month)
        month_days = calendar.monthrange(month_date.year, month_date.month)[1]
        payer_id = re.search(r'(?<=PayerAccountId=)[^,]+', msg).group(0)
        last_modified = re.search(r'(?<=S3KeyLastModified=)"[^,]+"', msg).group(0)

        statement_total = 0
        for az in billing_fixture.AZ_LIST:
            for account_index, account in enumerate(billing_fixture.LINKED_ACCOUNTS):

                msg_act = msg
                msg_act = self.rex_linked_account_id.sub(account["id"], msg_act)

                for day in range(month_days):
                    start_date = billing_utils.get_month_day(month, day + 1)
                    end_date = start_date + datetime.timedelta(hours=1)

                    # billing item for generic services
                    for item_index, item in enumerate(self.sample_billing_items):
                        r = self._get_item_random(account_index, item_index, day)
                        msg_line = msg_act

                        msg_line = self._build_msg(az, msg_line, r, start_date, end_date, item[0], item[1], item[2], 'N', None, None)

                        out += billing_utils.build_event(end_date, month_date, template_msg, msg_line)


                    # billing item for instance
                    for _ in range(24):
                        for instance_i, instance in enumerate(billing_fixture.INSTANCE_LIST):
                            r = self._get_item_random(account_index, instance_i, day)
                            msg_line = msg_act
                            reserved = 'N'
                            cost = instance['cost']
                            desc = '"$%s per %s %s %s Instance Hour"' % (str(cost), instance['tenancy'], instance['platform'], instance['type'])
                            if r * 10 % 5 > 3:
                                reserved = 'Y'
                                cost = cost * 0.45
                                desc = '"USD %s hourly fee per %s (Amazon VPC), %s instance"' % (str(cost), instance['platform'], instance['type'])

                                if r * 10 % 6 > 4:
                                    desc = '"%s %s Spot Instance-hour in XXX in VPC Zone #X"' % (instance['type'], instance['platform'])


                            msg_line = self._build_msg(az, msg_line, r, start_date, end_date, 'Amazon Elastic Compute Cloud', 'RunInstances', 'BoxUsage:' + instance['type'], reserved, str(round(cost,8)), '1.00000000', desc)

                            for _ in range(int(r * 10 % 3 + 1)):
                                statement_total += round(cost, 8)
                                out += billing_utils.build_event(end_date, month_date, template_msg, msg_line)

                        start_date = start_date + datetime.timedelta(hours=1)
                        end_date = end_date + datetime.timedelta(hours=1)

        statement_total_msg = self.rex_payer_id.sub(payer_id, self.sample_statement_total)
        statement_total_msg = self.rex_s3key.sub(last_modified, statement_total_msg)

        start_date = billing_utils.get_month_day(month, 1)
        end_date = start_date + datetime.timedelta(hours=1)
        out += billing_utils.build_event(end_date, month_date, template_msg, statement_total_msg)

        return out


if __name__ == "__main__":
    detailed_billing = BaseDetailedBilling(object)
    m = {
        'index': 'hello',
        'sourcetype': 'b',
        'host': '1',
        '_raw': 'InvoiceID=#INVOICE_ID#, PayerAccountId=#PAYER_ID#, LinkedAccountId=#LINKED_ACCOUNT_ID#, RecordType=LinkedLineItem, RecordId=#RECORD_ID#, ProductName=#PRODUCT_NAME#, RateId=#RATE_ID#, SubscriptionId=#SUBSCRIPTION_ID#, PricingPlanId=#PLAN_ID#, UsageType=#USAGE_TYPE#, Operation=#OPERATION#, AvailabilityZone=#AZ#, ReservedInstance=#RESERVED_INSTANCE#, ItemDescription=#ITEM_DESCRIPTION#, UsageStartDate=#START_YMD#, UsageEndDate=#END_YMD#, UsageQuantity=#QUANTITY#, BlendedCost=#BLENDED_COST#, ResourceId=#RESOURCE_ID#, user:Name=#TAG_NAME#, user:env=#TAG_ENV#, S3KeyLastModified="#NOW#"'
    }
    print detailed_billing.generate_billing(m, 1)

