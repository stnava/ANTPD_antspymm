####################################################################################
# ANTPD Processing Script
# This script prepares and processes multimodal MRI data for the ANTPD project
####################################################################################

import os
import sys
import glob
import re
import pandas as pd
import ants
import antspyt1w
import antspymm

# ------------------------------------------------------------------------------
# Environment setup
# ------------------------------------------------------------------------------
# Set thread usage for TensorFlow and ITK
num_threads = '24'
os.environ["TF_NUM_INTEROP_THREADS"] = num_threads
os.environ["TF_NUM_INTRAOP_THREADS"] = num_threads
os.environ["ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS"] = num_threads

# ------------------------------------------------------------------------------
# Define base data directory, with fallback if needed
# ------------------------------------------------------------------------------
base_directory = "/mnt/cluster/data/ANTPD/"
rootdir = os.path.join(base_directory, "bids/")

if not os.path.exists(rootdir):
    base_directory = "/workspace/data/ANTPD/"
    rootdir = os.path.join(base_directory, "bids/")

print(f"Using rootdir: {rootdir}")

if not os.path.exists(rootdir):
    print("ERROR: Could not locate rootdir. Please check path.")
    sys.exit(1)

# ------------------------------------------------------------------------------
# Load normalization template or download if missing
# ------------------------------------------------------------------------------
template_path = os.path.expanduser("~/.antspymm/PPMI_template0.nii.gz")

if os.path.exists(template_path):
    template = ants.image_read(template_path)
else:
    print("Template file not found. Downloading default template...")
    antspyt1w.get_data(force_download=True)
    antspymm.get_data(force_download=True)
    template = ants.image_read(template_path)

# Apply brain mask and crop
brain_mask = ants.image_read(os.path.expanduser("~/.antspymm/PPMI_template0_brainmask.nii.gz"))
template = template * brain_mask
template = ants.crop_image(template, ants.iMath(brain_mask, "MD", 12))

print("Template loaded and processed. Ready for test run.")

# ------------------------------------------------------------------------------
# Locate all T1-weighted files and select based on input index
# ------------------------------------------------------------------------------
t1fns = glob.glob(os.path.join(rootdir, "*", "*", "anat", "*T1w.nii.gz"))
t1fns.sort()

# Get file index from command line, default to 9
fileindex = int(sys.argv[1]) if len(sys.argv) > 1 else 9

if fileindex >= len(t1fns):
    print("ERROR: File index out of range.")
    sys.exit(1)

t1fn = t1fns[fileindex]
print(f"Selected T1 file: {t1fn}")

# ------------------------------------------------------------------------------
# Prepare output directories
# ------------------------------------------------------------------------------
newoutdir = os.path.join(base_directory, 'antpd_antspymm')
csvoutdir = os.path.join(base_directory, 'studycsvs')
os.makedirs(newoutdir, exist_ok=True)
os.makedirs(csvoutdir, exist_ok=True)

# ------------------------------------------------------------------------------
# Extract subject ID and session from filename
# ------------------------------------------------------------------------------
filename_base = os.path.basename(t1fn)
subject_id, subdate = filename_base.split("_")[:2]
print(f"RUN: subject = {subject_id}, session = {subdate}")

# ------------------------------------------------------------------------------
# Verify T1 file exists
# ------------------------------------------------------------------------------
anatfn = t1fn
if not os.path.exists(anatfn):
    print(f"ERROR: T1 file does not exist: {anatfn}")
    sys.exit(1)

# ------------------------------------------------------------------------------
# Locate DWI and resting-state BOLD files
# ------------------------------------------------------------------------------
dwi_pattern = os.path.join(rootdir, subject_id, subdate, 'dwi', '*dwi.nii.gz')
dwi_files = glob.glob(dwi_pattern)
dtfn = [dwi_files[0]] if dwi_files else []

func_pattern = os.path.join(rootdir, subject_id, subdate, 'func', '*rest_bold.nii.gz')
func_files = glob.glob(func_pattern)
rsfn = [func_files[0]] if func_files else []

# ------------------------------------------------------------------------------
# Generate and save study CSV
# ------------------------------------------------------------------------------
studycsv = antspymm.generate_mm_dataframe(
    projectID='ANTPD',
    subjectID=subject_id,
    date=subdate,
    imageUniqueID='000',
    modality='T1w',
    source_image_directory=rootdir,
    output_image_directory=newoutdir,
    t1_filename=anatfn,
    dti_filenames=dtfn,
    rsf_filenames=rsfn
)

csv_filename = os.path.join(csvoutdir, f"{subject_id}_{subdate}.csv")
studycsv.to_csv(csv_filename)

# ------------------------------------------------------------------------------
# Run multimodal processing pipeline
# ------------------------------------------------------------------------------
studycsv_clean = studycsv.dropna(axis=1)

mmrun = antspymm.mm_csv(
    studycsv_clean,
    dti_motion_correct='SyN',
    dti_denoise=True,
    normalization_template=template,
    normalization_template_output='ppmi',
    normalization_template_transform_type='antsRegistrationSyNQuickRepro[s]',
    normalization_template_spacing=[1, 1, 1],
    mysep='_'
)

print("Multimodal processing complete.")
