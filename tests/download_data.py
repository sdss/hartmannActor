#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author: José Sánchez-Gallego (gallegoj@uw.edu)
# @Date: 2019-12-30
# @Filename: download_data.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

# flake8: noqa

import os
import sys
import urllib.request


sys.path.append(os.path.dirname(__file__) + '/../')  # To allow absolute import

from tests.test_boss_collimate import *


BASE_URL = 'https://data.sdss.org/sas/dr16/apo/'


files = {
    focused_dir: [focused1, focused2, notFocused1, notFocused2],
    badFFS_dir: [badFFS_1, badFFS_2],
    noLight_dir: [noLight1, noLight2],
    sparsePlug_dir: [sparsePlug1, sparsePlug2]
}


def download_data():

    os.chdir(os.path.dirname(__file__))

    for dir_ in files:

        dest_dir = dir_
        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir)

        for file_ in files[dir_]:

            # Download all the cameras regardless of the specific file.
            expand_files = []
            for camera in ['r1', 'b1', 'r2', 'b2']:
                chunks = file_.split('-')
                chunks[1] = camera
                expand_files.append('-'.join(chunks))

            for camera_file in expand_files:
                url = os.path.join(BASE_URL, dir_, camera_file)
                dest_file = os.path.join(dest_dir, camera_file)

                if not os.path.exists(dest_file):
                    print(f'Downloading {url} to {dest_file} ...')
                    urllib.request.urlretrieve(url, dest_file)


if __name__ == '__main__':
    download_data()
