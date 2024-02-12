# ANTPD_antspymm

ANTsPyMM processing for ANTPD

this brief collection of scripts should be used as a guideline for how to 
run ANTsPyMM on your own data. it is neither exhaustive nor perfect but 
provides the basic idea.  it was developed for a slurm cluster - you may 
need to modify things here for your own compute environment. the home 
directory on the cluster was: `/mnt/cluster/data/ANTPD`.

NOTE: `ANTPD` MRI appears to have several problems that the data curators are aware of but have not resolved.  Nevertheless, we use the data gratefully because of its availability and potential future relevance when the current (Feb 2024) issues are remedied.

the steps to recreate the processing include:

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

    * rejoice in the thousands of useful quantitative neuroimaging variables you easily produced and merged in a single data frame.

5.  fuse the output of step 4 with demographics ( not covered here )

example output data is in the `data` directory - including a few of the QC figures that are generated.  these can be viewed via:

```bash
open `find ./data/antpd_antspymm/ -name "*brain.png"`
open `find ./data/antpd_antspymm/ -name "*FAbetter.png"`
open `find ./data/antpd_antspymm/ -name "*DefaultMode.png"`
```

Look at correlations among inter-modality variables.

```R
dd=read.csv("data/antpd_antspymm.csv")
cc=dd[,"DTI_mean_fa.body_of_corpus_callosum.jhu_icbm_labels_1mm"]
mtg=dd[,"T1Hier_thk_left_middle_temporaldktcortex"]
# inter network correlation
dfn=dd[,"rsfMRI_fcnxpro122_DefaultB_2_SalVentAttnB"]
fd=dd[,"rsfMRI_fcnxpro122_FD_mean"]
plot( cc, mtg )
cor.test( cc, mtg ) # ~0.74
plot( cc, dfn )
cor.test( cc, dfn ) # ~0.26
plot( mtg, dfn )
cor.test( mtg, dfn ) # ~0.6

dd$bv = dd$T1Hier_vol_hemisphere_lefthemispheres + dd$T1Hier_vol_hemisphere_righthemispheres

# example joint model
summary( lm( rsfMRI_fcnxpro122_DefaultB_2_SalVentAttnB ~ 
    rsfMRI_fcnxpro122_FD_mean+
    DTI_mean_fa.body_of_corpus_callosum.jhu_icbm_labels_1mm + T1Hier_thk_left_middle_temporaldktcortex , data=dd ) )



```