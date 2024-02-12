#!/bin/bash
ID=`pwd`
ID=`basename $ID`
echo $ID
echo TASK ID is $SLURM_ARRAY_TASK_ID
python3 /mnt/cluster/data/${ID}/src/slurm/02_job_script.py $SLURM_ARRAY_TASK_ID
