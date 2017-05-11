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
# PlexxiBeat is a Python script that acts as a Plexxi Control client, retrieves specific information from the
# Plexxi Control instance, and inserts it into an Elastic Search database.
# ES tools like Kibana can then be used to visualize this information.

from __future__ import print_function
import sys, time
import json
from subprocess import Popen, PIPE
import argparse

# Command line options exist to override all of these
debug = 1
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

	if args.debug > 1:
		print("debug2: ", time.strftime("%H:%M:%S"))
	fabric = switch.getAllSwitchFabrics()[0]
	if args.debug > 1:
		print("debug2: ", time.strftime("%H:%M:%S"))
	outports = fabric.getAllSwitchFabricOutPorts()
	if args.debug > 1:
		print("debug2: ", time.strftime("%H:%M:%S"))
	totalFabricPorts = 0
	totalPeerPorts = 0
	peerList = []
	for port in outports:
		if debug > 1:
			print("debug: port = ", port)
		if not port.isAccessPort():
			totalFabricPorts = totalFabricPorts + 1
			peerPorts = port.getAllPeerSwitchPorts()
			if debug > 1:
				print("debug: peerPorts = ", peerPorts)
			totalPeerPorts = totalPeerPorts + len(peerPorts)
	return (totalPeerPorts, totalFabricPorts)


#
# pushToElasticSearch(object)
#
# Pushes a JSON object into Elastic Search
#
def pushToElasticSearch(jsonObject):
	"""
	Takes a JSON object and inserts it into Elastic Search
	"""

	if (push):
		if (debug):
			print("debug: pushing data to:", eshost, "using username", esuser, "and password", espassword)
		esurl = 'http://' + args.eshost + ':9200/plexxi-beat/external?pretty'
		esuserpass = args.esuser + ':' + args.espassword
		p = Popen([
			args.curl,
			'-XPOST',
			'-u',
			esuserpass,
			'-d',
			jsonObject,
			esurl
		],
			stdin=PIPE,
			stdout=PIPE,
			stderr=PIPE)
		output, err = p.communicate()
		return (p.returncode)
	else:
		return (0)


#
# getFabricInfo(plexxiFabric)
#
# Collect info and stats for a specific fabric (element from PlexxiRing.getAll())
#
def getFabricInfo(plexxiFabric):
	"""
	Get a set of fabric stats and basic info for a specific fabric element
	return a JSON object with the data collected
	"""

	fabric = {}
	fabric['fabric'] = plexxiFabric.getName()
	fabric['whole'] = plexxiFabric.isWhole()
	fabric['stable'] = plexxiFabric.isStable()
	switchList = []
	for sw in plexxiFabric.getAllPlexxiSwitchesInRing():
		switchList.append(str(sw.getName()))
	fabric['switches'] = {'count': len(switchList), 'names': switchList}
	fabric['type'] = "plexxi-fabric"
	fabric['@timestamp'] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
	fabric['control'] = args.host
	return (fabric)


def getSwitchInfo(plexxiSwitch):
	"""
	Get a set of switch stats and basic info for a given switch
	return a JSON object with the data collected
	"""

	switch = {}
	if args.debug > 1:
		print("debug2: ", time.strftime("%H:%M:%S"))
	switch['type'] = "plexxi-switch"
	switch['@timestamp'] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
	switch['name'] = plexxiSwitch.getName()
	switch['status'] = plexxiSwitch.getStatus()
	switch['hwrev'] = plexxiSwitch.getPlexxiHwRevision()
	switch['ip-address'] = str(plexxiSwitch.getIpAddress())
	switch['productcode'] = plexxiSwitch.getProductCode()
	switch['lightrail'] = plexxiSwitch.getLightrailCount()
	switch['fabric'] = str(plexxiSwitch.getPlexxiRing())
	if args.debug > 1:
		print("debug2: ", time.strftime("%H:%M:%S"))
	cpustats = plexxiSwitch.showStatisticsLast(switchStatisticsType='CPU', format='CSV').split(",")
	switch['cpu'] = {'1m': float(cpustats[10]), '5m': float(cpustats[11]), '10m': float(cpustats[12])}
	memstats = plexxiSwitch.showStatisticsLast(switchStatisticsType='MEMORY', format='CSV').split(",")
	switch['memory'] = {'free': int(memstats[9]), 'total': int(memstats[10])}
	tempstats = plexxiSwitch.showStatisticsLast(switchStatisticsType='TEMPERATURE', format='CSV').split(",")
	switch['temp'] = {'cpu': float(tempstats[12]), 'fan': float(tempstats[14]), 'power': float(tempstats[15])}
	if args.debug > 1:
		print("debug2: ", time.strftime("%H:%M:%S"))
	(totalPeers, totalFabricPorts) = getSwitchPeers(plexxiSwitch)
	switch['peers'] = {'count': int(totalPeers)}
	switch['fabricports'] = int(totalFabricPorts)
	if args.debug > 1:
		print("debug2: ", time.strftime("%H:%M:%S"))
	switch['software'] = str(plexxiSwitch.getSwitchSoftwareVersion())
	switch['oper-status'] = str(plexxiSwitch.getOperationalStage())
	switch['control'] = args.host

	return (switch)


# Main

if __name__ == '__main__':

	# Parse arguments. Use defaults as defined above

	parser = argparse.ArgumentParser(prog='PlexxiBeat.py')
	parser.add_argument('--host', help='hostname of Plexxi Control instance', default=host)
	parser.add_argument('--user', help='user name for Plexxi Control instance', default=user)
	parser.add_argument('--password', help='password for Plexxi Control user', default=password)
	parser.add_argument('--push', type=int, help='do not push data into ElasticSearch', default=push)
	parser.add_argument('--curl', help='localion of "curl", default ' + curl, default=curl)
	parser.add_argument('--esuser', help='ElasticSearch username', default=esuser)
	parser.add_argument('--espassword', help='ElasticSearch password', default=espassword)
	parser.add_argument('--eshost', help='ElasticSearch host name', default=eshost)
	parser.add_argument('--debug', type=int, help='enable debug printing', default=debug)

	args = parser.parse_args()

	if (args.debug):
		print('debug: host =', args.host)
		print('debug: user =', args.user)
		print('debug: password =', args.password)
		print('debug: debug =', args.debug)
		print('debug: push =', args.push)
		print('debug: eshost = ', args.eshost)
		print('debug: esuser = ', args.esuser)
		print('debug: espassword = ', args.espassword)

	# construct the URL co connect to Plexxi Control and create a Session

	url = 'http://' + args.host + ':8080/PlexxiCore/api'
	session = CoreSession.connect(url, args.user, args.password)

	# First, get fabrics

	for i in PlexxiRing.getAll():

		if (args.debug):
			print("debug: collecting info for fabric:", i)

		fabric = getFabricInfo(i)

		if (args.debug):
			print("debug: collected: ", fabric)

		rc = pushToElasticSearch(json.dumps(fabric))

	# Next, get all switches and collect stuff for them

	switches = PlexxiSwitch.getAll()

	for sw in switches:

		if (args.debug):
			print("debug: collecting info for switch:", sw)

		switch = getSwitchInfo(sw)

		if (args.debug):
			print("debug: collected: ", switch)

		rc = pushToElasticSearch(json.dumps(switch))
