ID=`pwd`
ID=`basename $ID`
echo $ID
sbatch  --export=ALL --cpus-per-task 24  -o ~/slurmout/${ID}.%a.out  \
  --array=0-50  /mnt/cluster/data/${ID}/src/slurm/01_job_id_subscript.sh
