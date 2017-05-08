#!/usr/bin/env python2.7
# Copyright (c) 2015, Plexxi Inc. and its licensors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# PlexxiBeat.py version 0.1 - Marten Terpstra
#
# PlexxiBeat is a Perl script that acts as a Plexxi Control client, retrieves specific information from the Plexxi Control instance,
# and inserts it into an Elastic Search database. ES tools like Kibana can then be used to visualize this information.

from __future__ import print_function
import re, sys, os, time
import json
import subprocess
from subprocess import Popen, PIPE
import argparse

# Command line options exist to override all of these
debug = 0
host = 'plx-control-a1-1.ilab.plexxi.com'
user = 'admin'
password = 'plexxi'
push = 1
curl = '/usr/bin/curl'
esuser = 'plexxi'
espassword = 'plexxi'
eshost = 'elastic5.ilab.plexxi.com'

# make sure 2.7 site packegs can be included
sys.path.append('/opt/rh/python27/root/usr/lib/python2.7/site-packages')

# These are the Plexxi Control packages, it assumes this runs on a server/VM that has these bindings installed
# typically one would run these on the Control instance itself. At some point in the future this will be packaged
# as part of Plexxi Control

from plexxi.core.api.session import CoreSession
from plexxi.core.api.binding import PlexxiSwitchCpuStatistics, PlexxiSwitch, AlarmManager, PlexxiRing

# 
# getSwitchPeers(switch)
#
# for a given switch, return all peer ports. Used to count how many peers a switch has
#
def getSwitchPeers(switch):
    """                                                                                                                      
    Prints a list of switch Peers                                                                                            
    switchId - name or mac of switch, str 'All' for all switches                                                             
                                                                                                                             
    Goes through uplink (ring port) cable and prints the peer switch at the end of that cable                                
    This gives a complete map of switch uplink port to port connectivity through the Ring                                    
    """

    fabric = switch.getAllSwitchFabrics()[0]
    outports = fabric.getAllSwitchFabricOutPorts()
    totalFabricPorts = 0
    totalPeerPorts = 0
    for port in outports:
        if not port.isAccessPort():
            totalFabricPorts = totalFabricPorts + 1
            peerPorts = port.getAllPeerSwitchPorts()
            totalPeerPorts = totalPeerPorts + len(peerPorts)
    return(totalPeerPorts)


# Main

if __name__ == '__main__':
  parser = argparse.ArgumentParser(prog='PlexxiBeat.py')
  parser.add_argument('--host', help='hostname of Plexxi Control instance')
  parser.add_argument('--user', help='user name for Plexxi Control instance')
  parser.add_argument('--password', help='password for Plexxi Control user')
  parser.add_argument('--push', type=int, help='do not push data into ElasticSearch')
  parser.add_argument('--curl', help='localion of "curl", default '+curl)
  parser.add_argument('--esuser', help='ElasticSearch username')
  parser.add_argument('--espassword', help='ElasticSearch password')
  parser.add_argument('--eshost', help='ElasticSearch host name')
  parser.add_argument('--debug', type=int, help='enable debug printing')

  args = parser.parse_args()
  print(args)

  sys.exit()

  if (1):
    print('host =', host)
    print('user =', user)
    print('password =', password)
    print('debug =', debug)
    print('push =', push)
    print('eshost = ', eshost)
    print('esuser = ', esuser)
    print('espassword = ', espassword)

  url = 'http://' + host + ':8080/PlexxiCore/api'
  session = CoreSession.connect(url,user,password)

  for i in PlexxiRing.getAll():
      fabric = {}
      fabric['fabric'] = i.getName()
      fabric['whole'] = i.isWhole()
      fabric['stable'] = i.isStable()
      switchList = []
      for sw in i.getAllPlexxiSwitchesInRing():
          switchList.append(str(sw.getName()))
      fabric['switches'] = {'count': len(switchList), 'names': switchList}
      fabric['type'] = "plexxi-fabric"
      fabric['@timestamp'] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
      fabric['control'] = host
      fabric = json.dumps(fabric)

      if (debug):
          print(fabric)

      if (push):
          if (debug):
              print("debug: pushing data to:", eshost, "using username", esuser, "and password", espassword)
          esurl = 'http://' + eshost + ':9200/plexxi-beat/external?pretty'
          esuserpass = esuser + ':' + espassword
          p= Popen([
                  '/usr/bin/curl',
                  '-XPOST',
                  '-u',
                  esuserpass,
                  '-d',
                  fabric,
                  esurl
                  ],
                   stdin=PIPE,
                   stdout=PIPE,
                   stderr=PIPE)
          output, err = p.communicate()
          rc = p.returncode


  switches = PlexxiSwitch.getAll()
  for sw in switches:
      switch = {}
      switch['type'] = "plexxi-switch"
      switch['@timestamp'] = time.strftime("%Y-%m-%dT%H:%M:%S%z") 
      switch['name'] = sw.getName()
      switch['status'] = sw.getStatus()  
      switch['hwrev'] = sw.getPlexxiHwRevision()
      switch['ip-address'] = str(sw.getIpAddress())
      switch['productcode'] = sw.getProductCode()
      switch['lightrail'] = sw.getLightrailCount()
      switch['fabric'] = str(sw.getPlexxiRing())
      cpustats = sw.showStatisticsLast(switchStatisticsType = 'CPU', format='CSV').split(",")
      switch['cpu'] = {'1m': float(cpustats[10]), '5m': float(cpustats[11]), '10m': float(cpustats[12])}
      memstats = sw.showStatisticsLast(switchStatisticsType = 'MEMORY', format='CSV').split(",")
      switch['memory'] = {'free': int(memstats[9]), 'total': int(memstats[10])}
      tempstats = sw.showStatisticsLast(switchStatisticsType = 'TEMPERATURE', format='CSV').split(",")
      switch['temp'] = {'cpu': float(tempstats[12]), 'fan': float(tempstats[14]), 'power': float(tempstats[15])}
      switch['peers'] = {'count': int(getSwitchPeers(sw))}
      switch['software'] = str(sw.getSwitchSoftwareVersion())
      switch['oper-status'] =str(sw.getOperationalStage())
      switch['control'] = host
      switch = json.dumps(switch)

      if (debug):
          print(switch)

      if (push):
          if (debug):
                    print("debug: pushing data to:", eshost, "using username", esuser, "and password", espassword)
          p= Popen([
                  'curl',
                  '-XPOST',
                  '-u',
                  esuserpass,
                  '-d',
                  switch,
                  esurl,
                  ],
                   stdin=PIPE,
                   stdout=PIPE,
                   stderr=PIPE)
          output, err = p.communicate()
          rc = p.returncode


