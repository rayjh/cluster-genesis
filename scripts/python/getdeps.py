#!/usr/bin/env python
# Copyright 2019 IBM Corp.
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
import sys
import time
import os.path
import re
import code
import yaml

import lib.logger as logger
from lib.utilities import Color
import lib.genesis as gen

def main():
    log = logger.getlogger()
    log.debug('log this')
    dep_path = gen.get_dependencies_path()

    pre_list_file = [
                     'client_yum_pre_install.txt',
                     'client_pip_pre_install.txt',
                     'dlipy3_pip_pre_install.txt',
                     'dlipy2_pip_pre_install.txt',
                     'dlinsights_pip_pre_install.txt',
                     'dlipy3_conda_pre_install.txt',
                     'dlipy2_conda_pre_install.txt',
                     'dlinsights_conda_pre_install.txt',
                    ]

    def file_staging(list_file):

        env      = list_file.split('_',4)[0]
        function = list_file.split('_',4)[1]
        stage    = list_file.split('_',4)[0] +'_' + list_file.split('_',4)[1]
        return ([stage , function, env])


    for pre in pre_list_file:
        file_staging(pre)

        function = file_staging(pre)[1]
        stage    = file_staging(pre)[0]
        suffix   = 'install.txt'
        pre      = f'{stage}_pre_{suffix}'
        post     = f'{stage}_post_{suffix}'

        print (f'\nINFO - Current Stage   : {stage}\n'
               f'       Current Function: {function}\n')

        if function == 'yum':
# RPM
            try:
                with open(os.path.join(dep_path,pre), 'r') as f:
                    pre_rpm_pkgs = f.read().splitlines()
            except FileNotFoundError as exc:
                print(f'File not found: {dep_path}. Err: {exc}')

            try:
                with open(os.path.join(dep_path,post), 'r') as f:
                    post_rpm_pkgs = f.read().splitlines()
            except FileNotFoundError as exc:
                print(f'File not found: {dep_path}. Err: {exc}')

            pre_pkg_list = []
            for pkg in pre_rpm_pkgs:
                #found = re.search(r'([\w\.\-]+)\s+([\w\.\-\:]+)\s+([\w@\.\-]+)', pkg)
                pkg_items = pkg.split()
                pkg_fmt_name = ('- ' + pkg_items[0].rsplit('.', 1)[0] + '-' +
                                pkg_items[1] + '-' + pkg_items[0].rsplit('.', 1)[1])
                pre_pkg_list.append([pkg_fmt_name, pkg_items[2]])

            post_pkg_list = []
            repo_list = []
            for pkg in post_rpm_pkgs:
                pkg_items = pkg.split()
                rpm_repo = pkg_items[2]
                pkg_fmt_name = ('- ' + pkg_items[0].rsplit('.', 1)[0] + '-' +
                                pkg_items[1] + '.' + pkg_items[0].rsplit('.', 1)[1])
                post_pkg_list.append([pkg_fmt_name, rpm_repo])
                if rpm_repo not in repo_list:
                    repo_list.append(rpm_repo)

            for repo in repo_list:
                repo_pkgs = []
                for pkg in post_pkg_list:
                    if pkg[1] == repo and pkg not in pre_pkg_list:
                        repo_pkgs.append(pkg[0])
                for pkg in pre_pkg_list:
                    if pkg[1] == repo and pkg not in post_pkg_list:
                        repo_pkgs.append(pkg[0])

                try:
                    fname = repo.replace('/', '')
                    fname = fname.replace('@','')
                    fname = f'{stage}_{fname}_final.yml'
                    with open(os.path.join(dep_path, fname), 'w') as f:
                        f.write('\n'.join(repo_pkgs) + '\n')
                except FileNotFoundError as exc:
                    print(f'File not found: {fname}. Err: {exc}')

#pip

        elif function == 'pip':
            try:
                with open(os.path.join(dep_path,pre), 'r') as f:
                    pre_pip_pkgs = f.read().splitlines()
            except FileNotFoundError as exc:
                print(f'File not found: {dep_path}. Err: {exc}')

            try:
                with open(os.path.join(dep_path,post), 'r') as f:
                    post_pip_pkgs = f.read().splitlines()
            except FileNotFoundError as exc:
                print(f'File not found: {dep_path}. Err: {exc}')

            pre_pip_pkg_list = []
            for pkg in pre_pip_pkgs:
                pip_pkg_items = pkg.split()
                pip_pkg_fmt_name = (pip_pkg_items[0] + '==' +
                                    pip_pkg_items[1])
                pre_pip_pkg_list.append(pip_pkg_fmt_name)

            post_pip_pkg_list = []
            for pkg in post_pip_pkgs:
                pip_pkg_items = pkg.split()
                version = pip_pkg_items[1].replace('(','')
                version = version.replace(')','')
                pip_pkg_fmt_name = (pip_pkg_items[0] + '==' +
                                    version)
                post_pip_pkg_list.append(pip_pkg_fmt_name)

            pip_pkgs = []
            for pkg in post_pip_pkg_list:
                if pkg not in pre_pip_pkg_list:
                    pip_pkgs.append(pkg)
            for pkg in pre_pip_pkg_list:
                if pkg not in post_pip_pkg_list:
                    pip_pkgs.append(pkg)

            try:

                fname = f'{stage}_final.txt'
                with open(os.path.join(dep_path, fname), 'w') as f:
                    f.write('\n'.join(pip_pkgs) + '\n')
            except FileNotFoundError as exc:
                print(f'File not found: {fname}. Err: {exc}')

#conda
        elif function == 'conda':
            try:
                with open(os.path.join(dep_path,pre), 'r') as f:
                    pre_conda_pkgs = f.read().splitlines()
            except FileNotFoundError as exc:
                print(f'File not found: {dep_path}. Err: {exc}')

            try:
                with open(os.path.join(dep_path,post), 'r') as f:
                    post_conda_pkgs = f.read().splitlines()
            except FileNotFoundError as exc:
                print(f'File not found: {dep_path}. Err: {exc}')

            pre_conda_pkg_list = []
            for pkg in pre_conda_pkgs:
                conda_pkg_items = pkg.split()
                conda_repo = conda_pkg_items[3].rsplit('/',1)[1]
                conda_pkg_fmt_name = (conda_pkg_items[0] + '-' + conda_pkg_items[1] +
                                      '-' + conda_pkg_items[2] + '.tar.bz2')
                pre_conda_pkg_list.append([conda_pkg_fmt_name,conda_repo])

            post_conda_pkg_list = []
            conda_repo_list = []
            for pkg in post_conda_pkgs:
                conda_pkg_items = pkg.split()
                try:
                    conda_repo = conda_pkg_items[-1].rsplit('/',1)[1]
                    if conda_repo:
                        conda_pkg_fmt_name = (conda_pkg_items[0] + '-' + conda_pkg_items[1] +
                                              '-' + conda_pkg_items[2] + '.tar.bz2')
                        post_conda_pkg_list.append([conda_pkg_fmt_name,conda_repo])
                except IndexError:
                    conda_repo = "pip_pkgs"
                    conda_pkg_fmt_name = (conda_pkg_items[0] + '==' + conda_pkg_items[1])
                    post_conda_pkg_list.append([conda_pkg_fmt_name,conda_repo])
                if conda_repo not in conda_repo_list:
                    conda_repo_list.append(conda_repo)


            for conda_repo in conda_repo_list:
                conda_pkgs = []
                for conda_pkg in post_conda_pkg_list:
                    if conda_pkg[1] == conda_repo and conda_pkg not in pre_pkg_list:
                        conda_pkgs.append(conda_pkg[0])
                for conda_pkg in pre_conda_pkg_list:
                    if conda_pkg[1] == conda_repo and conda_pkg not in post_pkg_list:
                        conda_pkgs.append(conda_pkg[0])


                try:
                    fname = conda_repo.replace(' ', '')
                    fname = f'{stage}_{fname}_final.txt'
                    with open(os.path.join(dep_path, fname), 'w') as f:
                        f.write('\n'.join(conda_pkgs) + '\n')
                except FileNotFoundError as exc:
                    print(f'File not found: {fname}. Err: {exc}')
        else:
            print ("Error - No Function Found.")

    def package_merge():

        for pre in pre_list_file:
            file_staging(pre)

            fenv = file_staging(pre)[2]
            ffunction = file_staging(pre)[1]

            if fenv != 'client':

                if ffunction == 'pip':
                    ffname = f'{fenv}_{ffunction}_final.txt'
                    fcname = f'{ffunction}_consolidated.yml'
                    try:
                        with open(os.path.join(dep_path,ffname), 'r') as finput:
                            print (f'\nINFO - Consolidating {ffunction} packages\n')
                            print (f'       File name: {ffname}\n')
                            with open(os.path.join(dep_path,fcname),'a') as foutput:
                                for line in finput:
                                    foutput.write(line)

                    except FileNotFoundError as exc:
                        pass

                if ffunction == 'conda':
                    conda_pkgs = ['main', 'free', 'conda_forge', 'conda_pkgs']
                    for pkg in conda_pkgs:
                        ffname = f'{fenv}_{ffunction}_{pkg}_final.txt'
                        fcname = f'{ffunction}_consolidated.yml'
                        try:
                            with open(os.path.join(dep_path,ffname), 'r') as finput:
                                print ('\nINFO - Consolidating pip packages')
                                print (f'       File name: {ffname}\n')
                                with open(os.path.join(dep_path,fcname),'a') as foutput:
                                    foutput.write(f'\n-----{fenv} conda repository: {pkg}\n')
                                    for line in finput:
                                        foutput.write(line)
                        except FileNotFoundError as exc:
                            pass

                if ffunction == 'conda':
                    conda_pkgs = ['pip_pkgs']
                    for pkg in conda_pkgs:
                        ffname = f'{fenv}_{ffunction}_{pkg}_final.txt'
                        fcname = f'{ffunction}_pip_consolidated.yml'
                        try:
                            with open(os.path.join(dep_path,ffname), 'r') as finput:
                                print ('\nINFO - Consolidating pip packages')
                                print (f'       File name: {ffname}\n')
                                with open(os.path.join(dep_path,fcname),'a') as foutput:
                                    foutput.write(f'----- {fenv} conda repository: pip-pkgs\n')
                                    for line in finput:
                                        foutput.write(line)
                        except FileNotFoundError as exc:
                            pass
    package_merge()

    def reslove_duplicates():
        fclist = ['conda','pip','conda_pip']
        for i in fclist:
            fcname = f'{i}_consolidated.yml'
            lines_seen = set()
            outfile = open(os.path.join(dep_path,f'{i}.yml'), "w")
            for line in open(os.path.join(dep_path,fcname),"r"):
                if line not in lines_seen:
                    outfile.write(f'- {line}')
                    lines_seen.add(line)
        #code.interact(banner='here', local=dict(globals(), **locals()))
    #reslove_duplicates()

    def pkg_list_format():
        print("\nINFO - Searching for pkg list template file\n")

        pkg_list_path = gen.GEN_SOFTWARE_PATH
        pkg_list_name = 'pkg-lists-tmplate.yml'
        tmp_pkg_list_path = os.path.join(pkg_list_path,f'{pkg_list_name}')
        try:
            print(f"\nINFO - Loading {pkg_list_name} data \n")
            load_tmp = open(f'{tmp_pkg_list_path}')
            with load_tmp as f:
                grab = yaml.load(f)

                conda_forge = grab['conda_forge_noarch_pkgs']['accept_list']
                anaconda_free =  grab['anaconda_free_pkgs']['accept_list']
                anaconda_main = grab['anaconda_main_pkgs']['accept_list']
                python3 = grab['python3_specific_pkgs']
                python = grab['python_pkgs']
                epel = grab['epel_pkgs']
                yum = grab['yum_pkgs']
                cuda = grab['cuda_pkgs']

        except FileNotFoundError as exc:
                print(f'File not found: {pkg_list_name}. Err: {exc}')

        yum_files = [
                     'client_yum_anaconda7.5_final.yml',
                     'client_yum_cuda-powerup_final.yml',
                     'client_yum_dependencies-powerup_final.yml',
                     'client_yum_epel-ppc64le-powerup_final.yml',
                     'client_yum_installed_final.yml',
                     ]

        for yum_file in yum_files:
            try:
                yum_path = dep_path + '/' + yum_file
                print(f"\nINFO - Loading {yum_file} data \n")
                load_yum_yml = open(f'{yum_path}')
                with load_yum_yml as f:
                    grab_yum = yaml.load(f)

                    base = yum_file.split('_',3)[2]

                    code.interact(banner='yum files', local=dict(globals(), **locals()))

                    if base == 'epel-ppc64le-powerup':
                        pass
                        epel = grab['epel_pkgs']

                    elif base == 'cuda-powerup':
                        pass
                        cuda = grab['cuda_pkgs']

                    else:
                        pass
                        yum = grab['yum_pkgs']

            except FileNotFoundError as exc:
                    print(f'File not found: {yum_file}. Err: {exc}')


        conda_file = 'conda.yml'
        conda_file_path = dep_path + '/conda.yml'
        try:
            print(f"\nINFO - Loading {conda_file} data \n")
            load_conda_yml = open(f'{conda_file_path}')
            with load_conda_yml as f:
                grab_conda = yaml.load(f)

                code.interact(banner='conda file', local=dict(globals(), **locals()))

        except FileNotFoundError as exc:
                print(f'File not found: {conda_file}. Err: {exc}')


        pip_file = 'pip.yml'
        pip_file_path = dep_path + '/pip.yml'
        try:
            print(f"\nINFO - Loading {pip_file} data \n")
            load_pip_yml = open(f'{pip_file_path}')
            with load_pip_yml as f:
                grab_pip = yaml.load(f)

                code.interact(banner='pip files', local=dict(globals(), **locals()))

        except FileNotFoundError as exc:
                print(f'File not found: {pip_file}. Err: {exc}')



    pkg_list_format()

if __name__ == '__main__':
    """Simple python template
    """

    logger.create('nolog', 'info')
    log = logger.getlogger()

    main()
    print("\nINFO - Process Completed\n")
