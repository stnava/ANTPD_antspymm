# ANTPD_antspymm

ANTsPyMM processing for ANTPD

this brief collection of scripts should be used as a guideline for how to 
run ANTsPyMM on your own data. it is neither exhaustive nor perfect but 
provides the basic idea.  it was developed for a slurm cluster - you may 
need to modify things here for your own compute environment. the home 
directory on the cluster was: `/mnt/cluster/data/ANTPD`.

the steps include:

1.  clone this repo 

2.  clone the ANTPD data via `bash src/download.sh`

    * the data comes from [this link](https://openneuro.org/datasets/ds001907/versions/3.0.2)

    * data will look like: `/mnt/cluster/data/ANTPD/bids/sub-RC4107/ses-2/anat/sub-RC4107_ses-2_T1w.nii.gz` once it's finished downloading

    * alternatively, you can download only one subject "by hand" e.g. try `sub-RC4111/ses-1` who has useful T1, rsfMRI and DTI and then modify steps below for this single case.

3.  run the job `bash src/slurm/00_high_level_batch_call.sh`

    * make sure the threads per job variable is what you want for your environment 

    * make sure that variable matches the `nth` variable in `src/slurm/02_job_script.py`

        * this would be the script to run on a single subject 

4.  when all subjects are done, run `python3 src/agg.py`

    * rejoice in the thousands of useful quantitative neuroimaging variables you easily produced.

5.  merge the output of step 4 with demographics ( not covered here )

