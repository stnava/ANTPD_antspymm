#!/usr/bin/env python

#
# This gets ANTsXNet data and pretrained networks,
# and downloads SIQ super-resolution models from Figshare.
#

import sys
import os
import zipfile
import tempfile
import urllib.request

import antspynet

def download_siq_superres_models(target_dir):
    """
    Downloads the SIQ reference super-resolution models from Figshare
    and extracts them to the target directory.
    """
    figshare_url = "https://figshare.com/ndownloader/articles/27079987/versions/1"
    target_zip_path = os.path.join(target_dir, "siq_superres_models.zip")

    print(f"Downloading SIQ models from {figshare_url} to {target_zip_path}")
    urllib.request.urlretrieve(figshare_url, target_zip_path)

    print(f"Extracting SIQ models into {target_dir}")
    with zipfile.ZipFile(target_zip_path, 'r') as zip_ref:
        zip_ref.extractall(target_dir)

    os.remove(target_zip_path)
    print("SIQ super-resolution models downloaded and extracted.")


import os
import urllib.request
import zipfile

def download_pymm():
    import pathlib

    target_dir = os.path.expanduser("~/.antspymm/")
    os.makedirs(target_dir, exist_ok=True)

    figshare_urls = [
        "https://ndownloader.figshare.com/articles/14766102/versions/46",
        "https://figshare.com/ndownloader/articles/16912366/versions/25"
    ]

    for i, url in enumerate(figshare_urls, start=1):
        zip_filename = f"pymm_models_{i}.zip"
        target_zip_path = os.path.join(target_dir, zip_filename)

        print(f"Downloading PyMM from {url} to {target_zip_path}")
        urllib.request.urlretrieve(url, target_zip_path)

        print(f"Extracting PyMM models into {target_dir}")
        with zipfile.ZipFile(target_zip_path, 'r') as zip_ref:
            zip_ref.extractall(target_dir)

        os.remove(target_zip_path)

    print("✅ PyMM models downloaded and extracted.")


# -------------------------- MAIN SCRIPT --------------------------
if (len(sys.argv) == 1):
    usage = '''
  Usage: {} /path/to/ANTsXNetData [doInstall=1] [dataList.txt] [networkList.txt]

  Second argument can be passed to skip installation in docker files.

  Subsequent arguments, if specified, read a list of things to fetch from a text file.
  This can be used to get a subset of the data / networks.

  Downloads ANTsXNet data and networks to the specified directory.

  The path MUST be absolute or it will be interpreted relative to
  the default ~/.keras
'''
    print(usage.format(sys.argv[0]))
    sys.exit(1)

# Base output dir
output_dir = sys.argv[1]
os.makedirs(output_dir, exist_ok=True)

do_install = 1
if len(sys.argv) > 2:
    do_install = int(sys.argv[2])
if do_install == 0:
    sys.exit(0)

download_pymm()

# Download SIQ super-resolution models
download_siq_superres_models(output_dir)

# ANTsXNet data
data_path = os.path.join(output_dir, "ANTsXNet")
os.makedirs(data_path, exist_ok=True)

all_data = list()
if len(sys.argv) > 3:
    with open(sys.argv[3]) as f:
        all_data = f.read().splitlines()
else:
    all_data = list(antspynet.get_antsxnet_data('show'))
    if 'show' in all_data:
        all_data.remove('show')

antspynet.set_antsxnet_cache_directory(data_path)

for entry in all_data:
    print(f"Downloading ANTsXNet data: {entry}")
    try:
        antspynet.get_antsxnet_data(entry)
    except NotImplementedError:
        print(f"Failed to download {entry}")

# ANTsXNet pretrained networks
all_networks = list()
if len(sys.argv) > 4:
    with open(sys.argv[4]) as f:
        all_networks = f.read().splitlines()
else:
    all_networks = list(antspynet.get_pretrained_network('show'))
    for exclude in [
        'allen_brain_leftright_coronal_mask_weights',
        'allen_cerebellum_coronal_mask_weights',
        'allen_cerebellum_sagittal_mask_weights',
        'allen_sr_weights',
        'show'
    ]:
        if exclude in all_networks:
            all_networks.remove(exclude)

for entry in all_networks:
    print(f"Downloading pretrained network: {entry}")
    try:
        antspynet.get_pretrained_network(entry)
    except NotImplementedError:
        print(f"Failed to download {entry}")