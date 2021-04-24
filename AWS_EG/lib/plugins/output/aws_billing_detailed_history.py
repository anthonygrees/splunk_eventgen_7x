from __future__ import division
import sys
from shared.detailed_billing import BaseDetailedBilling

class AwsBillingDetailedCurrentPlugin(BaseDetailedBilling):
    name = 'aws_billing_detailed_current'

    def __init__(self, sample):
        BaseDetailedBilling.__init__(self, sample)

    def flush(self, q):
        if len(q) > 0:
            m = q.popleft()
            while m:
                # fill items
                for month in range(2, 13):
                    out = self.generate_billing(m, month)
                    print out
                    sys.stdout.flush()

                try:
                    m = q.popleft()
                except IndexError:
                    m = False


def load():
    """Returns an instance of the plugin"""
    return AwsBillingDetailedCurrentPlugin