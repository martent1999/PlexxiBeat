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
import argparse

# These are the Plexxi Control packages, it assumes this runs on a server/VM that has these bindings installed
# typically one would run these on the Control instance itself. At some point in the future this will be packaged
# as part of Plexxi Control


from plexxi.core.api.session import CoreSession
from plexxi.core.api.binding import PlexxiSwitch, PlexxiRing

from elasticsearch import Elasticsearch
# from elasticsearch.exceptions import TransportError
# from elasticsearch.helpers import bulk, streaming_bulk

# Command line options exist to override all of these
debug = 0
debugtime = 0
host = 'plx-control-a1-1.ilab.plexxi.com'
user = 'admin'
password = 'plexxi'
push = 1
curl = '/usr/bin/curl'
esuser = 'plexxi'
espassword = 'plexxi'
eshost = 'elastic5.ilab.plexxi.com'

# make sure 2.7 site packages can be included
sys.path.append('/opt/rh/python27/root/usr/lib/python2.7/site-packages')


#
# getSwitchPeers(switch)
#
# for a given switch, return all peer ports. Used to count how many peers a switch has
#
def get_switch_peers(plexxi_switch):
    """
    Prints a list of switch Peers
    switchId - name or mac of switch, str 'All' for all switches

    Goes through uplink (ring port) cable and prints the peer switch at the end of that cable
    This gives a complete map of switch uplink port to port connectivity through the Ring
    """

    if args.debugtime:
        print("time: getSwitchPeers-1", time.strftime("%H:%M:%S"))

    plexxi_fabric = plexxi_switch.getAllSwitchFabrics()[0]
    if args.debugtime:
        print("time: getSwitchPeers-2", time.strftime("%H:%M:%S"))

    outports = plexxi_fabric.getAllSwitchFabricOutPorts()
    if args.debugtime:
        print("time: time getSwitchPeers-3", time.strftime("%H:%M:%S"))
    total_fabric_ports = 0
    total_peer_ports = 0
    for port in outports:
        if args.debug > 2:
            print("debug2: port = ", port)
        if not port.isAccessPort():
            total_fabric_ports = total_fabric_ports + 1
            peer_ports = port.getAllPeerSwitchPorts()
            if args.debug > 1:
                print("debug2: peerPorts = ", peer_ports)
            total_peer_ports = total_peer_ports + len(peer_ports)
    if args.debug > 1:
        print("debug2: time getSwitchPeers-5", time.strftime("%H:%M:%S"))
    return total_peer_ports, total_fabric_ports


#
# pushToElasticSearch(object)
#
# Pushes a JSON object into Elastic Search
#
def push_to_elastic_search(esearch, data):
    """
    Takes a JSON object and inserts it into Elastic Search
    """

    if push:
        if debug:
            print("debug: pushing data to:", eshost, "using username", esuser, "and password", espassword)

        ret_value = esearch.index(index='plexxi-beat-' + time.strftime("%Y.%m-%d"),
                                  doc_type="doc",
                                  body=data)

        return ret_value

    else:
        return 0


#
# getFabricInfo(plexxiFabric)
#
# Collect info and stats for a specific fabric (element from PlexxiRing.getAll())
#
def get_fabric_info(plexxi_fabric):
    """
    Get a set of fabric stats and basic info for a specific fabric element
    return a JSON object with the data collected
    """

    if args.debugtime:
        print("time: getFabricInfo-1", time.strftime("%H:%M:%S"))
    fabric_dict = dict()
    fabric_dict['fabric'] = plexxi_fabric.getName()
    fabric_dict['whole'] = plexxi_fabric.isWhole()
    fabric_dict['stable'] = plexxi_fabric.isStable()
    switch_list = []
    for plexxi_switch in plexxi_fabric.getAllPlexxiSwitchesInRing():
        switch_list.append(str(plexxi_switch.getName()))
    fabric_dict['switches'] = {'count': len(switch_list), 'names': switch_list}
    fabric_dict['type'] = "plexxi-fabric"
    fabric_dict['@timestamp'] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    fabric_dict['control'] = args.host
    if args.debugtime:
        print("time: getFabricInfo-2", time.strftime("%H:%M:%S"))
    return fabric_dict


def get_switch_info(plexxi_switch):
    """
    Get a set of switch stats and basic info for a given switch
    return a JSON object with the data collected
    """

    if args.debugtime:
        print("time: getSwitchInfo-1", time.strftime("%H:%M:%S"))
    switch_dict = dict()
    switch_dict['type'] = "plexxi-switch"
    switch_dict['@timestamp'] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    switch_dict['name'] = plexxi_switch.getName()
    switch_dict['status'] = plexxi_switch.getStatus().value
    switch_dict['hwrev'] = plexxi_switch.getPlexxiHwRevision().value
    switch_dict['ip-address'] = str(plexxi_switch.getIpAddress())
    switch_dict['productcode'] = plexxi_switch.getProductCode().value
    switch_dict['lightrail'] = plexxi_switch.getLightrailCount()
    switch_dict['fabric'] = str(plexxi_switch.getPlexxiRing())
    if args.debugtime:
        print("time: getSwitchInfo-2", time.strftime("%H:%M:%S"))

    cpustats = plexxi_switch.showStatisticsLast(switchStatisticsType='CPU', format='CSV').split(",")
    if len(cpustats) > 13:
        switch_dict['cpu'] = {'1m': float(cpustats[10]), '5m': float(cpustats[11]), '10m': float(cpustats[12])}

    memstats = plexxi_switch.showStatisticsLast(switchStatisticsType='MEMORY', format='CSV').split(",")
    if len(memstats) > 10:
        switch_dict['memory'] = {'free': int(memstats[9]), 'total': int(memstats[10])}

    tempstats = plexxi_switch.showStatisticsLast(switchStatisticsType='TEMPERATURE', format='CSV').split(",")
    if len(memstats) > 15:
        switch_dict['temp'] = {'cpu': float(tempstats[12]), 'fan': float(tempstats[14]), 'power': float(tempstats[15])}

    (totalPeers, totalFabricPorts) = get_switch_peers(plexxi_switch)
    if args.debugtime:
        print("time: getSwitchInfo-3", time.strftime("%H:%M:%S"))
    switch_dict['peers'] = {'count': int(totalPeers)}
    switch_dict['fabricports'] = int(totalFabricPorts)
    switch_dict['software'] = str(plexxi_switch.getSwitchSoftwareVersion())
    switch_dict['oper-status'] = str(plexxi_switch.getOperationalStage().value)
    switch_dict['control'] = args.host

    if args.debugtime:
        print("time: getSwitchInfo-2", time.strftime("%H:%M:%S"))

    return switch_dict


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
    parser.add_argument('--debugtime', type=int, help="enable timing output printing", default=debugtime)

    args = parser.parse_args()

    if args.debug:
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

    # Create elasticsearch instance
    es = Elasticsearch([args.eshost], port=9200)

    # First, get fabrics
    for i in PlexxiRing.getAll():

        if args.debug:
            print("debug: collecting info for fabric:", i)

        fabric = get_fabric_info(i)

        if args.debug:
            print("debug: collected: ", fabric)

        rc = push_to_elastic_search(es, fabric)

    # Next, get all switches and collect stuff for them

    switches = PlexxiSwitch.getAll()

    for sw in switches:

        if args.debug:
            print("debug: collecting info for switch:", sw)

        switch = get_switch_info(sw)

        if args.debug:
            print("debug: collected: ", switch)

        rc = push_to_elastic_search(es, switch)
