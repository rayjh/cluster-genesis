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
from pyghmi import exceptions as pyghmi_exception

from lib.inventory import Inventory
import lib.logger as logger
import lib.bmc as _bmc


def set_power_clients(state, config_path=None, client_list=None, max_attempts=5,
                      wait=6):
    """Set power on or off for multiple clients
    Args:
        state (str) : 'on' or 'off'
        client_list (list of str): list of IP addresses
    """
    log = logger.getlogger()
    inv = Inventory(config_path)
    wait = float(wait)
    max_attempts = int(max_attempts)

    if not client_list:
        log.debug('Retrieving IPMI address list from inventory')
        client_list = inv.get_nodes_ipmi_ipaddr(0)

    clients_left = client_list[:]
    attempt = 0

    none_cnt = 0
    for client in client_list:
        if client is None:
            none_cnt += 1
            log.warning('client node ip address is "None"')
            clients_left.remove(None)

    clients_left.sort()
    while clients_left and attempt < max_attempts:
        nodes = {}
        attempt += 1
        if attempt > 1:
            print('Retrying set power {}. Attempt {} of {}'
                  .format(state, attempt, max_attempts))
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
                        log.error(f'Failed IPMI login attempt {i}, rack: {rack_id} '
                                  f'BMC {ipv4}')
                        time.sleep(1)
                        del tmp

        for client in clients_left:
            if client in bmc_dict:
                log.debug(f'Setting power state to {state}. '
                          f'Device: {client}')
                status = bmc_dict[client].chassis_power(state, wait)
                if status:
                    if attempt in [2, 4, 8]:
                        print(f'{client} - Power status: {status}')
                    # Allow delay between turn on to limit power surge
                    if state == 'on':
                        time.sleep(0.5)
                else:
                    log.error(f'Failed attempt {attempt} set power {state} '
                              f'for node {client}')

        time.sleep(wait + attempt)

        for client in clients_left:
            if client in bmc_dict:
                status = bmc_dict[client].chassis_power('status')
                if status:
                    if attempt in [2, 4, 8]:
                        print(f'{client} - Power status: {status}, '
                              f'required state: {state}')
                    if status == state:
                        log.debug(f'Successfully set power {state} for node {client}')
                        clients_set += [client]
                else:
                    log.error(f'Failed attempt {attempt} get power {state} '
                              f'for node {client}')

        for client in clients_set:
            clients_left.remove(client)

        if attempt == max_attempts and clients_left:
            log.error('Failed to power {} some clients'.format(state))
            log.error(clients_left)

        del bmc_dict

    log.info('Powered {} {} of {} client devices.'
             .format(state, len(client_list) - (len(clients_left) + none_cnt),
                     len(client_list)))

    if state == 'off':
        print('Pausing 60 sec for client power off')
        time.sleep(60)

    if clients_left:
        return False
    return True


if __name__ == '__main__':
    """
    """
    logger.create()
    parser = argparse.ArgumentParser()
    parser.add_argument('state', default='none',
                        help='Boot device.  ie network or none...')

    parser.add_argument('config_path',
                        help='Config file path.')

    parser.add_argument('client_list', default='', nargs='*',
                        help='List of ip addresses.')

    parser.add_argument('max_attempts', default='2', nargs='*',
                        help='Max number of login / power attempts')

    parser.add_argument('--print', '-p', dest='log_lvl_print',
                        help='print log level', default='info')

    parser.add_argument('--file', '-f', dest='log_lvl_file',
                        help='file log level', default='info')

    args = parser.parse_args()

    if args.log_lvl_print == 'debug':
        print(args)

    set_power_clients(args.state, args.config_path, args.client_list,
                      max_attempts=args.max_attempts)
