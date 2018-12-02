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

import os.path
import datetime

from lib.switch_common import SwitchCommon
from lib.genesis import GEN_PASSIVE_PATH, GEN_PATH


class Arista(SwitchCommon):
    """Class for configuring and retrieving information for a Cisco
    Nexus switches running NX-OS.  This class developed on Cisco 5020.
    Cisco IOS switches may work or may need some methods overridden.
    This class can be instantiated in 'active' mode, in which case the
    switch will be configured or in 'passive' mode in which case the
    commands needed to configure the switch are written to a file.
    When in passive mode, information requests will return 'None'.
    In passive mode, a filename can be generated which
    will contain the active mode switch commands used for switch
    configuration. This outfile will be written to the
    'cluster-genesis/passive' directory if it exists or to the
    'cluster-genesies' directory if the passive directory does not
    exist. If no outfile name is provided a default name is used.
    In active mode, the 'host, userid and password named variables
    are required. If 'mode' is not provided, it is defaulted to 'passive'.

    Args:
        host (string): Management switch management interface IP address
        or hostname or if in passive mode, a fully qualified filename of the
        acquired mac address table for the switch.
        userid (string): Switch management interface login user ID.
        password (string): Switch management interface login password.
        mode (string): Set to 'passive' to run in passive switch mode.
            Defaults to 'active'
        outfile (string): Name of file to direct switch output to when
        in passive mode.
    """
    SEP = '\n'
    ENABLE_REMOTE_CONFIG = f'en{SEP}configure terminal {SEP} '
    ENABLE_REMOTE_CONFIG += ' {} '
    #IFC_ETH_CFG = 'interface ethernet {} '
    #IFC_PORT_CH_CFG = 'interface port-channel {} '
    #NO_IFC_PORT_CH_CFG = 'no interface port-channel {} '
    #PORT_PREFIX = 'Eth'
    #SHOW_VLANS = 'show vlan'
    #CREATE_VLAN = 'vlan {}'
    #DELETE_VLAN = 'no vlan {}'
    #SHOW_PORT = 'show interface brief'
    #CLEAR_MAC_ADDRESS_TABLE = 'clear mac address-table dynamic'
    SHOW_MAC_ADDRESS_TABLE = f'show mac address-table {SEP}'

    def __init__(self, host=None, userid=None,
                 password=None, mode=None, outfile=None):
        self.mode = mode
        self.host = host
        if self.mode == 'active':
            self.userid = userid
            self.password = password
        elif self.mode == 'passive':
            if os.path.isdir(GEN_PASSIVE_PATH):
                self.outfile = GEN_PASSIVE_PATH + '/' + outfile
            else:
                self.outfile = GEN_PATH + '/' + outfile
            f = open(self.outfile, 'a+')
            f.write(str(datetime.datetime.now()) + '\n')
            f.close()
        super(Arista, self).__init__(host, userid, password, mode, outfile)


class switch(object):
    @staticmethod
    def factory(host=None, userid=None, password=None, mode=None, outfile=None):
        return Arista(host, userid, password, mode, outfile)
