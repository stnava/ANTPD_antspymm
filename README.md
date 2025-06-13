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

    * use variables from the aggregated data frame such as `subjectID` and `date` to guide this process.

    * take a look at `T1Hier_resnetGrade` and associated `png` images to get a quick look through the data.

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

# brain volume
dd$bv = dd$T1Hier_vol_hemisphere_lefthemispheres + dd$T1Hier_vol_hemisphere_righthemispheres
dd$bv = dd$bv/mean(dd$bv)

```

## simlr example


```r
library( ANTsR )
library( subtyper )

# Define the URL of the raw CSV file
url <- "https://raw.githubusercontent.com/stnava/ANTPD_antspymm/main/data/antpd_antspymm.csv"

# Read the CSV file into R
data <- read.csv(url)[,-1]

head(names(data))

datapym = antspymm_predictors( data, TRUE )
simfile = "/tmp/EXAMPLE"
if ( ! file.exists( paste0(simfile,'_t1_simlr.csv') ) ) {
    # could do something else here - this is just based on quality
    trainer = subtyper::fs(
        data$T1Hier_resnetGrade > 1.1 ) 
    print(table(trainer))
    mysimN = log_parameters(
        antspymm_simlr,
        logfile=path.expand(simfile),
        blaster=datapym,
        select_training_boolean=trainer, 
        energy='cca',
        nsimlr=4,
        doAsym=2,
#        sparseness=0.90,
        covariates=c('T1Hier_resnetGrade '),  # optional confounds
        exclusions=c("fcnxpro134","fcnxpro129",'mean_md' ,'area','thk'),  # filter some variable types out
        returnidps=F,
        verbose=T )
    write_simlr_data_frames( mysimN$simlrX$v, path.expand(simfile)  )
}

measure_types = c("t1","t1a", "dt", "dta", "rsf" ) 
presim=read_simlr_data_frames( path.expand(simfile), 
    measure_types )
npc = ncol(presim[[1]])
simproj = apply_simlr_matrices( datapym, presim,
   absolute_value = rep( TRUE, length( measure_types ) ),
   robust=FALSE )
tempcolsOrig = simproj[[2]] # names of the simlr variables


```



## Docker 

Build the container with the Dockerfile that is included within this repository.

```bash
docker build -t antspymm-test .
```

Run the container

```bash
docker run -it -v $(pwd)/data:/workspace/data antspymm-test /bin/bash
```

Within the container, do:

```bash 
cd ANTPD_antspymm
python3 src/slurm/02_job_script.py 2 # run the nth subject
```

this will produce a single example run reproducibly.

you made need to increase the memory available to your docker container for this to work.  the example has been run successfully with 48GB of memory.  the primary need for this amount of memory is (i believe) the dipy tensor reconstruction step.


all together now

```bash
docker run -it -v $(pwd)/data:/workspace/data antspymm-test /bin/bash
cd ANTPD_antspymm
python3 src/slurm/02_job_script.py 12 # run the nth subject
```
