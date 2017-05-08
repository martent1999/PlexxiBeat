# PlexxiBeat
Part of Plexxi Clarity, grab data on fabrics and switches and insert into ElasticSearch

$ ./PlexxiBeat.py --help

usage: PlexxiBeat.py [-h] [--host HOST] [--user USER] [--password PASSWORD]

                     [--push PUSH] [--curl CURL] [--esuser ESUSER]

                     [--espassword ESPASSWORD] [--eshost ESHOST]

                     [--debug DEBUG]


optional arguments:

  -h, --help            show this help message and exit

  --host HOST           hostname of Plexxi Control instance

  --user USER           user name for Plexxi Control instance

  --password PASSWORD   password for Plexxi Control user

  --push PUSH           do not push data into ElasticSearch

  --curl CURL           localion of "curl", default /usr/bin/curl

  --esuser ESUSER       ElasticSearch username

  --espassword ESPASSWORD
                        ElasticSearch password

  --eshost ESHOST       ElasticSearch host name

  --debug DEBUG         enable debug printing


Sample Output (when not pushed into ElasticSearch, and debug turned on):


$ ./PlexxiBeat.py --push 0 --debug 1 --host plx-control-a1-1.ilab.plexxi.com

host = plx-control-a1-1.ilab.plexxi.com

user = admin

password = plexxi

debug = 1

push = 0

eshost =  elastic5.ilab.plexxi.com

esuser =  plexxi

espassword =  plexxi

{"control": "plx-control-a1-1.ilab.plexxi.com", "fabric": "PlexxiFabric", "whole": true, "@timestamp": "2017-05-08T10:47:54-0400", "switches": {"count": 4, "names": ["1.6", "1.9", "1.8", "1.7"]}, "stable": true, "type": "plexxi-fabric"}

{"status": "HEALTHY", "productcode": "SWITCH_2E", "peers": {"count": 12}, "software": "3.2.0-a2", "name": "1.7", "temp": {"fan": 0.0, "cpu": 35.0, "power": 21.0}, "oper-status": "OperationalStage.S3P", "@timestamp": "2017-05-08T10:47:54-0400", "control": "plx-control-a1-1.ilab.plexxi.com", "fabric": "03734100041a00007ec6a5e4873c9faa (PlexxiFabric)", "ip-address": "172.24.1.7", "memory": {"total": 3733327872, "free": 236322816}, "hwrev": "CEL_REDSTONE_XP", "type": "plexxi-switch", "cpu": {"5m": 1.60156, "1m": 1.62891, "10m": 1.51172}, "lightrail": 0}

{"status": "HEALTHY", "productcode": "SWITCH_2E", "peers": {"count": 8}, "software": "3.2.0-a2", "name": "1.9", "temp": {"fan": 0.0, "cpu": 42.0, "power": 22.0}, "oper-status": "OperationalStage.S3P", "@timestamp": "2017-05-08T10:47:59-0400", "control": "plx-control-a1-1.ilab.plexxi.com", "fabric": "03734100041a00007ec6a5e4873c9faa (PlexxiFabric)", "ip-address": "172.24.1.9", "memory": {"total": 3733327872, "free": 1042477056}, "hwrev": "CEL_REDSTONE_XP", "type": "plexxi-switch", "cpu": {"5m": 1.51172, "1m": 1.55078, "10m": 1.41016}, "lightrail": 0}

{"status": "HEALTHY", "productcode": "SWITCH_2E", "peers": {"count": 20}, "software": "3.2.0-a2", "name": "1.8", "temp": {"fan": 0.0, "cpu": 37.0, "power": 22.0}, "oper-status": "OperationalStage.S3P", "@timestamp": "2017-05-08T10:48:02-0400", "control": "plx-control-a1-1.ilab.plexxi.com", "fabric": "03734100041a00007ec6a5e4873c9faa (PlexxiFabric)", "ip-address": "172.24.1.8", "memory": {"total": 3733327872, "free": 2164178944}, "hwrev": "CEL_REDSTONE_XP", "type": "plexxi-switch", "cpu": {"5m": 1.48828, "1m": 1.60938, "10m": 1.48047}, "lightrail": 0}

{"status": "HEALTHY", "productcode": "SWITCH_2E", "peers": {"count": 16}, "software": "3.2.0-a2", "name": "1.6", "temp": {"fan": 0.0, "cpu": 34.0, "power": 21.0}, "oper-status": "OperationalStage.S3P", "@timestamp": "2017-05-08T10:48:05-0400", "control": "plx-control-a1-1.ilab.plexxi.com", "fabric": "03734100041a00007ec6a5e4873c9faa (PlexxiFabric)", "ip-address": "172.24.1.6", "memory": {"total": 3733327872, "free": 2238410752}, "hwrev": "CEL_REDSTONE_XP", "type": "plexxi-switch", "cpu": {"5m": 1.05078, "1m": 0.89063, "10m": 1.21094}, "lightrail": 0}
