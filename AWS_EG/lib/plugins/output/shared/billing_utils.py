import datetime
import calendar
import time
from xml.sax.saxutils import escape

MONTH_DAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

def _minus_months(month, day = 1):
    sourcedate = datetime.datetime.now()
    sourcedate = datetime.datetime(sourcedate.year, sourcedate.month, day)
    month = sourcedate.month - 1 - month
    year = int(sourcedate.year + month / 12 )
    month = month % 12 + 1
    day = min(sourcedate.day,calendar.monthrange(year,month)[1])
    return datetime.datetime(year,month,day)

def get_start_date(month, day = 1):
    end_date = _minus_months(month, day)
    return end_date.strftime("%Y/%m/%d")

def get_s3key(month, day = 1):
    end_date = _minus_months(month, day)
    return end_date.strftime("%Y-%m-%dT%H:%M:%S") + '.000Z'

def get_start_datetime(month, day = 1):
    end_date = _minus_months(month, day)
    return end_date.strftime("%Y-%m-%d %H:%M:%S")

def get_end_datetime(month, day = 1):
    end_date = _minus_months(month, day)
    return end_date.strftime("%Y-%m-%d %H:%M:%S")

def get_start_month(month, day = 1):
    end_date = _minus_months(month, day)
    return end_date.strftime("%Y-%m")

def get_end_date(month, day = 1):
    end_date = _minus_months(month, day)
    strftStr = "%Y/%m/" + str(MONTH_DAYS[end_date.month - 1])
    return end_date.strftime(strftStr)

def get_end_timestamp(month, day = 1):
    end_date = _minus_months(month, day)
    end_date = datetime.datetime(end_date.year, end_date.month, MONTH_DAYS[end_date.month - 1])
    return time.mktime(end_date.timetuple())


def get_month_day(prev_month, day = 1):
    now = datetime.datetime.now().date()
    month = now.month
    year = now.year

    if month - prev_month < 1:
        month = 12 + (month - prev_month)
        year -= 1
    else:
        month -= prev_month

    return datetime.datetime(year, month, day)

def build_event(end_date, month_date, template_msg, msg, isDetailed = True):
    prefix = 's3://aws-billing-detailed-line-items-with-resources-and-tags-%s.csv.zip' if isDetailed else 's3://aws-cost-allocation-%s.csv'

    event_str  = '  <event>\n'
    event_str += '    <time>%s</time>\n' % time.mktime(end_date.timetuple())
    event_str += '    <index>%s</index>\n' % template_msg['index']
    event_str += '    <source>%s</source>\n' % (prefix % month_date.strftime('%Y-%m'))
    event_str += '    <sourcetype>%s</sourcetype>\n' % template_msg['sourcetype']
    event_str += '    <host>%s</host>\n' % template_msg['host']
    event_str += '    <data>%s</data>\n' % escape(msg)
    event_str += '  </event>\n'
    return event_str