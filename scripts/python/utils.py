#!/usr/bin/env python
# Copyright 2018 IBM Corp.
#
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import nested_scopes, generators, division, absolute_import, \
    with_statement, print_function, unicode_literals

from netaddr import IPNetwork
import argparse
from subprocess import Popen, PIPE
import sys
# from time import sleep

from lib.config import Config
import lib.logger as logger
# import lib.genesis as gen


def _sub_proc_exec(cmd):
    data = Popen(cmd.split(), stdout=PIPE, stderr=PIPE)
    stdout, stderr = data.communicate()
    return stdout, stderr

def _sub_proc_launch(cmd, stdout=PIPE, stderr=PIPE):
    data = Popen(cmd.split(), stdout=PIPE, stderr=PIPE)
    return data

def scan_ping_network(network_type='all', config_path=None):
    cfg = Config()
    type_ = cfg.get_depl_netw_client_type()
    # print(type_)
    if network_type == 'pxe' or network_type == 'all':
        net_type = 'pxe'
        idx = type_.index(net_type)
        cip = cfg.get_depl_netw_client_cont_ip()[idx]
        netprefix = cfg.get_depl_netw_client_prefix()[idx]
        cidr_cip = IPNetwork(cip + '/' + str(netprefix))
        net_c = str(IPNetwork(cidr_cip).network)
        cmd = 'fping -a -r0 -g ' + net_c + '/' + str(netprefix)
        result, err = _sub_proc_exec(cmd)
        print(result)

    if network_type == 'ipmi' or network_type == 'all':
        net_type = 'ipmi'
        idx = type_.index(net_type)
        cip = cfg.get_depl_netw_client_cont_ip()[idx]
        netprefix = cfg.get_depl_netw_client_prefix()[idx]
        cidr_cip = IPNetwork(cip + '/' + str(netprefix))
        net_c = str(IPNetwork(cidr_cip).network)
        cmd = 'fping -a -r0 -g ' + net_c + '/' + str(netprefix)
        result, err = _sub_proc_exec(cmd)
        print(result)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--scan-pxe-network',
                        action='store_true',
                        default=False,
                        help='Name of utility function to run')

    parser.add_argument('--scan-ipmi-network',
                        action='store_true',
                        default=False,
                        help='Name of utility function to run')

    parser.add_argument('--print', '-p', dest='log_lvl_print',
                        help='print log level', default='info')

    parser.add_argument('--file', '-f', dest='log_lvl_file',
                        help='file log level', default='info')

    args = parser.parse_args()

    logger.create(args.log_lvl_print, args.log_lvl_file)

    if args.scan_pxe_network:
        scan_ping_network('pxe')

    if args.scan_ipmi_network:
        scan_ping_network('ipmi')
