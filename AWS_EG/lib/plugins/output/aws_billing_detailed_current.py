from __future__ import division
import sys
from shared.detailed_billing import BaseDetailedBilling

class AwsBillingDetailedCurrentPlugin(BaseDetailedBilling):
    name = 'aws_billing_detailed_current'

    def __init__(self, sample):
        BaseDetailedBilling.__init__(self, sample)

    def flush(self, q):
        out = ''
        if len(q) > 0:
            m = q.popleft()
            while m:
                # fill items
                out += self.generate_billing(m, 1)

                try:
                    m = q.popleft()
                except IndexError:
                    m = False

        print out
        sys.stdout.flush()

def load():
    """Returns an instance of the plugin"""
    return AwsBillingDetailedCurrentPlugin