# Splunk EventGen 7x
This repo installs `eventgen` v7x on your Splunk Instance and then creates data.  
  
### Event Config
You can configure and set up the events in the `eventgen.conf` file.  
  
The interval and count will control how many records are created.
  
```bash
[aws.contactlens.s3]
index = main
interval = 60
count = 10
earliest = -60m
latest = now
sourcetype = aws:contactlens:s3
timezone = local

token.0.token = (##full_date##)
token.0.replacementType = timestamp
token.0.replacement = %Y%m%d

token.1.token = (##year##)
token.1.replacementType = timestamp
token.1.replacement = %Y

token.2.token = (##month##)
token.2.replacementType = timestamp
token.2.replacement = %m
```
  
### Sample Data
The sample data is held in the `samples` folder.  You can set dynamic variables and replace timestamp and names.  
  
The variables will replace `##year##` and `##month##` with `timestamp`.  
  
```json
{"InputS3Uri":"s3://connect-2c18b5fbca70/connect/splunkgsa/CallRecordings/##year##/##month##/##day##/c04b9f56-069a-4baa-8cbf-cbd10b3b5da3_##full_date##T19:42_UTC.wav","ContactId":"c04b9f56-069a-4baa-8cbf-cbd10b3b5da3","InstanceId":"f50483e1-9ee4-4836-b3f1-a78d52f41269"}
```
  
### More Details
The code - https://github.com/splunk/eventgen  
  
 - Splunk Tutorial - http://splunk.github.io/eventgen/TUTORIAL.html  
 - Full Reference - http://splunk.github.io/eventgen/REFERENCE.html#eventgenconfspec  
 - Great Blog - https://rav3n.medium.com/splunk-eventgen-quick-tutorial-593f526bafc1  