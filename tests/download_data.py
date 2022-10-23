#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author: José Sánchez-Gallego (gallegoj@uw.edu)
# @Date: 2019-12-30
# @Filename: download_data.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

import os
import urllib.request


BASE_URL = "https://data.sdss.org/sas/dr17/apo/"


def download_data():

    cwd = os.path.dirname(__file__)
    files = open(os.path.join(cwd, "data/files.dat"), "r").read().splitlines()

    downloaded_dir = os.path.join(cwd, "data/downloaded")
    if not os.path.exists(downloaded_dir):
        os.mkdir(downloaded_dir)

    for file_ in files:
        file_ = file_.strip()
        if file_ == "" or file_.startswith("#"):
            continue

        url = os.path.join(BASE_URL, file_)
        dest_file = os.path.join(downloaded_dir, os.path.basename(file_))

        if not os.path.exists(dest_file):
            print(f"Downloading {url} to {dest_file} ...")
            urllib.request.urlretrieve(url, dest_file)


if __name__ == "__main__":
    download_data()
