from __future__ import division
import sys
from shared.monthly_billing import BaseMonthlyBilling


class AwsBillingMonthlyCurrentPlugin(BaseMonthlyBilling):
    name = 'aws_billing_monthly_current'
    MAXQUEUELENGTH = 10

    def __init__(self, sample):
        BaseMonthlyBilling.__init__(self, sample)

    def flush(self, q):
        out = ""
        if len(q) > 0:
            m = q.popleft()
            while m:
                out += self.generate_billing(m, 1)

                try:
                    m = q.popleft()
                except IndexError:
                    m = False

        print out
        sys.stdout.flush()

def load():
    """Returns an instance of the plugin"""
    return AwsBillingMonthlyCurrentPlugin