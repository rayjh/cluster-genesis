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


def _sub_proc_launch(cmd, stdout=PIPE, stderr=PIPE):
    data = Popen(cmd.split(), stdout=PIPE, stderr=PIPE)
    return data


def _sub_proc_exec(cmd, stdout=PIPE, stderr=PIPE):
    data = Popen(cmd.split(), stdout=PIPE, stderr=PIPE)
    stdout, stderr = data.communicate()
    return stdout, stderr

def _sub_proc_wait(proc):
    cnt = 0
    rc = None
    while rc is None:
        rc = proc.poll()
        print('\rwaiting for process to finish. Time elapsed: {:2}:{:2}:{:2}'.
              format(cnt // 3600, cnt % 3600 // 60, cnt % 60), end="")
        sys.stdout.flush()
        time.sleep(1)
        cnt += 1
    print('\n')
    resp, err = proc.communicate()
    print(resp)
    return rc

class remote_nginx_repo(object):
    def __init__(self, arch='ppc64le', rhel_ver='7'):
        self.repo_name = 'nginx repo'
        self.arch = arch
        self.rhel_ver = str(rhel_ver)
        self.log = logger.getlogger()

    def yum_create_remote(self):
        """Create the /etc/yum.repos.d/
        """
        self.log.info('Registering remote repo {} with yum.'.format(self.repo_name))
        repo_link_path = '/etc/yum.repos.d/nginx.repo'
        if os.path.isfile(repo_link_path):
            self.log.info('Remote linkage for repo {} already exists.'
                          .format(self.repo_name))
            self.log.info(repo_link_path)

        self.log.info('Creating remote repo link.')
        self.log.info(repo_link_path)
        with open(repo_link_path, 'w') as f:
            f.write('[nginx]\n')
            f.write('name={}\n'.format(self.repo_name))
            f.write('baseurl=http://nginx.org/packages/mainline/rhel/{}/{}\n'.format(self.rhel_ver, self.arch))
            f.write('gpgcheck=0\n')
            f.write('enabled=1\n')


class local_epel_repo(object):

    def __init__(self, repo_name, arch='ppc64le', rhel_ver='7'):
        self.repo_name = repo_name.lower()
        self.arch = arch
        self.rhel_ver = str(rhel_ver)
        self.log = logger.getlogger()

    def yum_create_local(self):
        """Create the /etc/yum.repos.d/
        """
        self.log.info('Registering local repo {} with yum.'.format(self.repo_name))

        repo_link_path = '/etc/yum.repos.d/{}-local.repo'.format(self.repo_name)
        if os.path.isfile(repo_link_path):
            self.log.info('Remote linkage for repo {} already exists.'
                          .format(self.repo_name))
            self.log.info(repo_link_path)

        self.log.info('Creating local repo link.')
        self.log.info(repo_link_path)
        with open(repo_link_path, 'w') as f:
            f.write('[{}-local]\n'.format(self.repo_name))
            f.write('name={}_local_repo\n'.format(self.repo_name))
            f.write('baseurl="file:///srv/repos/epel/{}/epel-{}/"\n'.format(self.rhel_ver, self.arch))
            f.write('gpgcheck=0')

    def sync(self):
        self.log.info('Syncing remote repository {}'.format(self.repo_name))
        self.log.info('This can take many minutes or hours for large repositories')
        cmd = 'reposync -a {} -r {} -p /srv/repos/epel/{} -l -m'.format(self.arch, self.repo_name, self.rhel_ver)
        #print(cmd)
        #cmd = 'sleep 5'
        proc = _sub_proc_launch(cmd)
        dat = proc.stdout.readline()
        print(dat)
        rc = _sub_proc_wait(proc)
        # code.interact(banner='sync_repo', local=dict(globals(), **locals()))
        if rc != 0:
            self.log.error(err)
        else:
            self.log.info('Process finished succesfully')

    def create_dirs(self):
        if not os.path.exists('/srv/repos/epel/{}'.format(self.rhel_ver)):
            self.log.info('creating directory /srv/repos/epel/{}'.format(self.rhel_ver))
            os.makedirs('/srv/repos/epel/{}'.format(self.rhel_ver))
        else:
            self.log.info('Directory /srv/repos/epel/{} already exists'.format(self.rhel_ver))

    def create(self):
        if not os.path.exists('/srv/repos/epel/{}/{}/repodata'.format(self.rhel_ver, self.repo_name)):
            self.log.info('Creating repository metadata and databases')
            cmd = 'createrepo -v -g comps.xml /srv/repos/epel/{}/{}'.format(self.rhel_ver, self.repo_name)
            print(cmd)
            proc = _sub_proc_launch(cmd)
            rc = _sub_proc_wait(proc)
            if rc != 0:
                self.log.error('Repo creation error: {}'.format(err))
            else:
                self.log.info('Repo create process finished succesfully')
        else:
            self.log.info('Repo {} already created'.format(self.repo_name))

    def yum_create_remote(self):
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
    """ setup reposities. sudo env "PATH=$PATH" python repo.py
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('repo_name', nargs=1,
                        help='repository name')

    parser.add_argument('--print', '-p', dest='log_lvl_print',
                        help='print log level', default='info')

    parser.add_argument('--file', '-f', dest='log_lvl_file',
                        help='file log level', default='info')

    args = parser.parse_args()
    args.repo_name = args.repo_name[0]

    if args.log_lvl_print == 'debug':
        print(args)

    logger.create(args.log_lvl_print, args.log_lvl_file)

    nginx_repo = remote_nginx_repo()
    nginx_repo.yum_create_remote()

    repo = local_epel_repo(args.repo_name)
    repo.yum_create_remote()
    repo.create_dirs()
    #repo.sync()
    repo.create()
    repo.yum_create_local()
