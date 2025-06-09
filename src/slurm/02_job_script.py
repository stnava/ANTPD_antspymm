####################################################################################
#
import os
from os.path import exists
import glob
import ants
import antspyt1w
import antspymm
#
#######################
# clean tmp # may be needed in context of much larger jobs
# import subprocess
# cmd_str = " find /tmp -ctime +1 -exec rm -rf {} +  "
# cmd_str = " sudo find /tmp  -amin +90 -delete "
# subprocess.run(cmd_str, shell=True)
# cmd_str = " du -h -d 1 /tmp "
# clean tmp done
#
####################################################################################
base_directory = "/mnt/cluster/data/ANTPD/"
rootdir = base_directory + "bids/"

# Check if the directory exists
if not os.path.exists(rootdir):
    # Fallback to alternative path
    base_directory = "/workspace/data/ANTPD/"
    rootdir = os.path.join(base_directory, "bids/")

print(f"Using rootdir: {rootdir}")

if not os.path.exists(rootdir):
    print("please fix the rootdir")
    sys.exit(0)

template_path = os.path.expanduser("~/.antspymm/PPMI_template0.nii.gz")

if os.path.exists(template_path):
    template = ants.image_read(template_path)
else:
    # Run fallback code here
    print("Template file not found. Running fallback procedure...")
    antspyt1w.get_data(force_download=True)
    antspymm.get_data(force_download=True)

print("ready for test run")

######################################################
# /mnt/cluster/data/ANTPD/bids/sub-RC4107/ses-2/anat/sub-RC4107_ses-2_T1w.nii.gz
t1fns = glob.glob( rootdir + "*/*/anat/*T1w.nii.gz" )
t1fns.sort()
import sys
fileindex = 9
if len( sys.argv ) > 1:
    fileindex = int(sys.argv[1])

if fileindex > len( t1fns ):
    sys.exit(0)

t1fn = t1fns[ fileindex ]
print("t1fn = " + t1fn)
import re
newoutdir = base_directory + 'antpd_antspymm/'
os.makedirs( newoutdir, exist_ok=True  )
os.makedirs( base_directory + 'studycsvs', exist_ok=True  )

subject_id = os.path.basename( t1fn )
splitit = subject_id.split( "_" )
subject_id = splitit[0]
subdate=splitit[1]
print( "RUN " + subject_id + " --- " + newoutdir + " " )
import antspymm

import os
nth='24'
os.environ["TF_NUM_INTEROP_THREADS"] = nth
os.environ["TF_NUM_INTRAOP_THREADS"] = nth
os.environ["ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS"] = nth
import sys
import pandas as pd
import glob
import ants
import antspymm


template = ants.image_read("~/.antspymm/PPMI_template0.nii.gz")
bxt = ants.image_read("~/.antspymm/PPMI_template0_brainmask.nii.gz")
template = template * bxt
template = ants.crop_image( template, ants.iMath( bxt, "MD", 12 ) )

anatfn = t1fn + '/anat/' + subject_id + "_T1w.nii.gz"
anatfn = t1fn 

if not os.path.exists( anatfn ) : # or not os.path.exists( dtfn ) or not os.path.exists( rsfn ):
    print( anatfn + " does not exist : exiting ")
    sys.exit(0)


# note: we explicitly only take the first run here
dwi_pattern = os.path.join(rootdir, subject_id, subdate, 'dwi', '*dwi.nii.gz')
dwi_files = glob.glob(dwi_pattern)

if dwi_files:
    dtfn = [dwi_files[0]]
else:
    dtfn = []
#    raise FileNotFoundError(f"No DWI file found for subject {subject_id} on {subdate} in {dwi_pattern}")

func_pattern = os.path.join(rootdir, subject_id, subdate, 'func', '*rest_bold.nii.gz')
func_files = glob.glob(func_pattern)

if func_files:
    rsfn = [func_files[0]]
else:
    rsfn = []
#    raise FileNotFoundError(f"No resting-state BOLD file found for subject {subject_id} on {subdate} in {func_pattern}")


# generate_mm_dataframe(projectID, subjectID, date, imageUniqueID, modality, source_image_directory, output_image_directory, t1_filename, flair_filename=[], rsf_filenames=[], dti_filenames=[], nm_filenames=[], perf_filename=[])

studycsv = antspymm.generate_mm_dataframe(
        'ANTPD',
        subject_id,
        subdate,
        '000',
        'T1w',
        rootdir,
        newoutdir,
        t1_filename = anatfn,
        dti_filenames = dtfn,
        rsf_filenames = rsfn
    )
studycsv.to_csv(base_directory + "studycsvs/" + subject_id + "_" + subdate + ".csv")
studycsv2 = studycsv.dropna(axis=1)
mmrun = antspymm.mm_csv(studycsv2,
                        dti_motion_correct='SyN',
                        dti_denoise=True,
                        normalization_template=template,
                        normalization_template_output='ppmi',
                        normalization_template_transform_type='antsRegistrationSyNQuickRepro[s]',
                        normalization_template_spacing=[1,1,1],
                        mysep='_')  # should be this

########################


