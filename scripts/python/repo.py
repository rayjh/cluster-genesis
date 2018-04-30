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

import argparse
import os
import sys
import time
import lib.logger as logger
from subprocess import Popen, PIPE
# import code

# from lib.genesis import GEN_PATH


class local_repo(object):

    def __init__(self, repo_name, arch='ppc64le', rhel_ver='7'):
        self.repo_name = repo_name.lower()
        self.arch = arch
        self.rhel_ver = str(rhel_ver)
        self.log = logger.getlogger()

    def _sub_proc_launch(self, cmd, stdout=PIPE, stderr=PIPE):
        data = Popen(cmd.split(), stdout=PIPE, stderr=PIPE)
        return data

    def _sub_proc_exec(self, cmd, stdout=PIPE, stderr=PIPE):
        data = Popen(cmd.split(), stdout=PIPE, stderr=PIPE)
        stdout, stderr = data.communicate()
        return stdout, stderr

    def create_local_link(self):
        self.log.info('Registering local repo {} with yum.'.format(self.repo_name))

        repo_link_path = '/etc/mum.repos.d/{}-local.repo'.format(self.repo_name)
        if os.path.isfile(repo_link_path):
            self.log.info('Remote linkage for repo {} already exists.'
                          .format(self.repo_name))
            self.log.info(repo_link_path)

        self.log.info('Creating remote repo link.')
        self.log.info(repo_link_path)
        with open(repo_link_path, 'w') as f:
            f.write('[{}-local]\n'.format(self.repo_name))
            f.write('name={}_local_repo\n'.format(self.repo_name))
            f.write('baseurl="file:///srv/repos/epel.staging/epel-{}/"\n'.format(self.arch))
            f.write('gpgcheck=0')

    def sync_repo(self):
        self.log.info('Syncing remote repository {}'.format(self.repo_name))
        self.log.info('This can take many minutes or hours for large repositories')
        cmd = 'reposync -a {} -r {} -p /srv/repos/epel.staging -l -m'.format(self.arch, self.repo_name)
        # resp, err = self._sub_proc_exec(cmd)
        proc = self._sub_proc_launch(cmd)
        # code.interact(banner='sync_repo', local=dict(globals(), **locals()))
        cnt = 1
        rc = None
        while rc is None:
            rc = proc.poll()
            print('\rwaiting for sync to finish. Time elapsed: min: {:3} sec: {:2}'.format(cnt // 60, cnt % 60), end="")
            sys.stdout.flush()
            time.sleep(1)
            cnt += 1
        print('\n')
        resp, err = proc.communicate()
        if rc != 0:
            self.log.error(err)
        else:
            self.log.info('Sync process finished succesfully')
        print(resp)

    def create_remote_link(self):
        self.log.info('Registering remote repo {} with yum.'.format(self.repo_name))

        repo_link_path = '/etc/mum.repos.d/{}.repo'.format(self.repo_name)
        if os.path.isfile(repo_link_path):
            self.log.info('Remote linkage for repo {} already exists.'
                          .format(self.repo_name))
            self.log.info(repo_link_path)

        self.log.info('Creating remote repo link.')
        self.log.info(repo_link_path)
        with open(repo_link_path, 'w') as f:
            f.write('[{}]\n'.format(self.repo_name))
            f.write('name=Extra Packages for Enterprise Linux {} - {}\n'.format(self.rhel_ver, self.arch))
            f.write('#baseurl=http://download.fedoraproject.org/pub/epel/{}/{}\n'.format(self.rhel_ver, self.arch))
            f.write('metalink=https://mirrors.fedoraproject.org/metalink?repo=epel-{}&arch={}\n'.format(self.rhel_ver, self.arch))
            f.write('failovermethod=priority\n')
            f.write('enabled=1\n')
            f.write('gpgcheck=1\n')
            f.write('gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-EPEL-{}\n'.format(self.rhel_ver))
            f.write('\n')
            f.write('[{}-debuginfo]\n'.format(self.repo_name))
            f.write('name=Extra Packages for Enterprise Linux {} - {} - Debug\n'.format(self.rhel_ver, self.arch))
            f.write('#baseurl=http://download.fedoraproject.org/pub/epel/{}/{}/debug\n'.format(self.rhel_ver, self.arch))
            f.write('metalink=https://mirrors.fedoraproject.org/metalink?repo=epel-debug-{}&arch={}\n'.format(self.rhel_ver, self.arch))
            f.write('failovermethod=priority\n')
            f.write('enabled=0\n')
            f.write('gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-EPEL-{}\n'.format(self.rhel_ver))
            f.write('gpgcheck=1\n')
            f.write('\n')
            f.write('[{}-source]\n'.format(self.repo_name))
            f.write('name=Extra Packages for Enterprise Linux {} - {} - Source\n'.format(self.rhel_ver, self.arch))
            f.write('#baseurl=http://download.fedoraproject.org/pub/epel/{}/SRPMS\n'.format(self.rhel_ver))
            f.write('metalink=https://mirrors.fedoraproject.org/metalink?repo=epel-source-{}&arch={}\n'.format(self.rhel_ver, self.arch))
            f.write('failovermethod=priority\n')
            f.write('enabled=0\n')
            f.write('gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-EPEL-{}\n'.format(self.rhel_ver))
            f.write('gpgcheck=1\n')


if __name__ == '__main__':
    """ Configures or deconfigures data switches.
    Args: optional log level or optional deconfig in any order
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('repo_name', nargs='?',
                        help='repository name',
                        default='config.yml')

    parser.add_argument('--print', '-p', dest='log_lvl_print',
                        help='print log level', default='info')

    parser.add_argument('--file', '-f', dest='log_lvl_file',
                        help='file log level', default='info')

    args = parser.parse_args()

    logger.create(args.log_lvl_print, args.log_lvl_file)

    repo = local_repo(args.repo_name)
    repo.create_remote_link()
    repo.sync_repo()
    repo.create_local_link()
