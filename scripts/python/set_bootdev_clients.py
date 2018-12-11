#!/usr/bin/env python3
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

import argparse
import time

from lib.inventory import Inventory
import lib.logger as logger
import lib.bmc as _bmc


def set_bootdev_clients(bootdev, persist=False, config_path=None, client_list=None,
                        max_attempts=5):
    log = logger.getlogger()
    inv = Inventory(cfg_file=config_path)

    if type(persist) is not bool:
        persist = (persist == 'True')

    # if client list passed, it is assumed to be pxe addresses.
    # otherwise use the entire ipmi inventory list. This allows a
    # subset of nodes to have their bootdev updated during install
    if not client_list:
        log.debug('Retrieving IPMI address list from inventory')
        client_list = inv.get_nodes_ipmi_ipaddr(0)
        clients_left = client_list[:]
    else:
        # Get corresponing ipmi addresses
        clients_left = []
        for index, hostname in enumerate(inv.yield_nodes_hostname()):
            ipv4_ipmi = inv.get_nodes_ipmi_ipaddr(0, index)
            ipv4_pxe = inv.get_nodes_pxe_ipaddr(0, index)
            if ipv4_pxe is not None and ipv4_pxe in client_list:
                clients_left.append(ipv4_ipmi)

    attempt = 0
    clients_left.sort()
    while clients_left and attempt < max_attempts:
        nodes = {}
        attempt += 1
        if attempt > 1:
            print('Retrying set bootdev. Attempt {} of {}'.format(attempt, max_attempts))
            print('Clients remaining: {}'.format(clients_left))
        clients_set = []
        bmc_dict = {}
        for index, hostname in enumerate(inv.yield_nodes_hostname()):
            ipv4 = inv.get_nodes_ipmi_ipaddr(0, index)
            if ipv4 is None or ipv4 not in clients_left:
                continue
            rack_id = inv.get_nodes_rack_id(index)
            userid = inv.get_nodes_ipmi_userid(index)
            password = inv.get_nodes_ipmi_password(index)
            bmc_type = inv.get_nodes_bmc_type(index)
            nodes[ipv4] = [rack_id, ipv4]
            if ipv4 in clients_left:
                for i in range(2):
                    tmp = _bmc.Bmc(ipv4, userid, password, bmc_type)
                    if tmp.is_connected():
                        bmc_dict[ipv4] = tmp
                        break
                    else:
                        log.error(f'Failed IPMI login attempt {i}, BMC {ipv4}')
                        time.sleep(1)
                        del tmp

        for client in clients_left:
            if client in bmc_dict:
                log.debug(f'Setting boot device to {bootdev}. '
                          f'Device: {client}')
                if bootdev in ('setup'):
                    status = bmc_dict[client].host_boot_mode(bootdev)
                else:
                    status = bmc_dict[client].host_boot_source(bootdev)

                if status:
                    if attempt in [2, 4, 8]:
                        print(f'{client} - Boot source: {status} Required source: '
                              f'{bootdev}')
                else:
                    log.error(f'Failed attempt {attempt} set boot source {bootdev} '
                              f'for node {client}')

        time.sleep(1 + attempt)

        for client in clients_left:
            if client in bmc_dict:
                if bootdev in ('setup'):
                    status = bmc_dict[client].host_boot_mode()
                else:
                    status = bmc_dict[client].host_boot_source()

                if status:
                    if attempt in [2, 4, 8]:
                        print(f'{client} - Boot source: {bootdev}')
                    if status == bootdev:
                        log.debug(f'Successfully set boot source to {bootdev} for '
                                  f'node {client}')
                        clients_set += [client]
                else:
                    log.error(f'Failed attempt {attempt} set host boot source to'
                              f'{bootdev} for node {client}')

                bmc_dict[client].logout()

        for client in clients_set:
            clients_left.remove(client)

        if attempt == max_attempts and clients_left:
            log.error('Failed to set boot device for some clients')
            log.debug(clients_left)

        del bmc_dict
    log.info('Set boot device to {} on {} of {} client devices.'
             .format(bootdev, len(client_list) - len(clients_left),
                     len(client_list)))


if __name__ == '__main__':
    """
    Arg1: boot device
    Arg2: persistence (boolean)
    Arg3: client list (specify None to use the entire client list)
    """
    logger.create()

    parser = argparse.ArgumentParser()
    parser.add_argument('bootdev', choices=['default', 'network', 'disk', 'setup'],
                        help='Boot device.  ie network or none...')

    parser.add_argument('--persist', action='store_true',
                        help='Persist this boot device setting.')

    parser.add_argument('config_path',
                        help='Boot device.  ie network or none...')

    parser.add_argument('client_list', default='', nargs='*',
                        help='List of ip addresses.')

    parser.add_argument('--print', '-p', dest='log_lvl_print',
                        help='print log level', default='info')

    parser.add_argument('--file', '-f', dest='log_lvl_file',
                        help='file log level', default='info')

    args = parser.parse_args()

    if args.log_lvl_print == 'debug':
        print(args)

    set_bootdev_clients(args.bootdev, args.persist, args.config_path, args.client_list)
