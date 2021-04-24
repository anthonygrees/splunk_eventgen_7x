from __future__ import division
from outputplugin import OutputPlugin
import datetime, time, re, random
import sys
from xml.sax.saxutils import escape

class AwsCloudwatchBillingCurrentPlugin(OutputPlugin):
    name = 'aws_cloudwatch_billing_current'
    MAXQUEUELENGTH = 10

    SERVICES = {
        'AWSDataTransfer': 0.6019, 
        'AmazonRoute53': 0.171,
        'awskms': 2.359,
        'AmazonKinesis': 2.676,
        'AmazonRDS': 16.3, 
        'AmazonSNS': 0.12, 
        'AmazonS3': 11.1,
        'AmazonCloudWatch': 6.6, 
        'AWSQueueService': 1.2, 
        'AmazonEC2': 206, 
        'AWSDirectoryService': 0.57, 
        'AmazonSimpleDB': 1.2, 
        'AmazonElastiCache': 3.4, 
        'AmazonDynamoDB': 10.23
    }

    linked_accounts = [
        "123456789",
        "729374374",
        "977474531",
        "988321849",
        "432784591"
    ]

    rex_account = re.compile(r'#ACCOUNT#')    
    rex_service = re.compile(r'#SERVICE#')
    rex_price = re.compile(r'#PRICE#')

    MONTHLY_VAR = 0.5
    DAILY_VAR = 0.1

    def _get_daily_random(self):
        now = datetime.datetime.now()
        now_month = now.year*100 + now.month
        now_day = now.year*10000 + now.month*100 + now.day

        random.seed(now_month)
        r = 1 - self.MONTHLY_VAR*0.5 + random.random()*self.MONTHLY_VAR

        random.seed(now_day)
        r = r * (1 - self.DAILY_VAR*0.5 + random.random()*self.DAILY_VAR)

        return r * now.day

    def __init__(self, sample):
        OutputPlugin.__init__(self, sample)

    def flush(self, q):
        # get random index of today
        r = self._get_daily_random()

        out = ""
        if len(q) > 0:
            m = q.popleft()
            while m:

                # replace
                msg = m['_raw']

                msg_act = msg

                now = datetime.datetime.now()
                billing_range = 65
                _time = now - datetime.timedelta(days=billing_range)

                for day in range(billing_range - 1):
                    _time = _time + datetime.timedelta(days=1)
                    timestamp = time.mktime(_time.timetuple())

                    for service in self.SERVICES:
                        msg = msg_act
                        price = self.SERVICES[service]
                        msg = self.rex_service.sub(service, msg)
                        msg = self.rex_price.sub(str((price+random.random()*_time.day) * _time.day), msg)

                        msg_temp = msg

                        for account in self.linked_accounts:
                            msg = msg_temp
                            msg = self.rex_account.sub(account, msg)

                            out += '  <event>\n'
                            out += '    <time>%s</time>\n' % str(timestamp)
                            out += '    <index>%s</index>\n' % m['index']
                            out += '    <source>%s</source>\n' % m['source']
                            out += '    <sourcetype>%s</sourcetype>\n' % m['sourcetype']
                            out += '    <host>%s</host>\n' % m['host']
                            out += '    <data>%s</data>\n' % escape(msg)
                            out += '  </event>\n'

                try:
                    m = q.popleft()
                except IndexError:
                    m = False

        print out
        sys.stdout.flush()

def load():
    """Returns an instance of the plugin"""
    return AwsCloudwatchBillingCurrentPlugin