# Define the fixture data for billing

LINKED_ACCOUNTS = [
    {"id": "123456789", "name": "IT"},
    {"id": "729374374", "name": "Development"},
    {"id": "977474531", "name": "Sales"},
    {"id": "988321849", "name": "HR"},
    {"id": "432784591", "name": "Support"}
]

# availability zone. Not distrubited gracefully, just for demo purpose
AZ_LIST = [
    ''
    'ap-southeast-1a',
    'ap-southeast-2a',
    'eu-central-1a',
    'sa-east-1a',
    'us-east-1a',
    'us-west-1a',
    'cn-north-1a',
    'us-gov-west-1a',
    'ap-northeast-1b',
    'ap-southeast-1b',
    'eu-central-1b',
    'us-west-2b',
    'cn-north-1b'
]


TAG_NAME_LIST = [
    '',
    'Sam',
    'Frank',
    'Peter',
    'Richard'
]

TAG_ENV_LIST = [
    '',
    'QA',
    'DEV',
    'MOBILE',
    'OPS',
    'SUPPORT'
]

INSTANCE_LIST = [
    { "type": "t2.large" , "cost": 0.104, "platform": "Linux", "tenancy": "On Demand" },
    { "type": "m3.large" , "cost": 0.12, "platform": "Linux", "tenancy": "On Demand"  },
    { "type": "m3.4xlarge" , "cost": 0.96, "platform": "Linux", "tenancy": "On Demand"  },
    { "type": "m4.4xlarge" , "cost": 0.958, "platform": "Linux", "tenancy": "On Demand"  },
    { "type": "c4.large" , "cost": 0.105, "platform": "Linux", "tenancy": "On Demand"  },
    { "type": "c3.4xlarge" , "cost": 0.84, "platform": "Linux", "tenancy": "Dedicated Usage"  },
    { "type": "r3.4xlarge" , "cost": 1.33, "platform": "Linux", "tenancy": "On Demand"  },
    { "type": "d2.8xlarge" , "cost": 5.52, "platform": "Linux", "tenancy": "On Demand"  },
]