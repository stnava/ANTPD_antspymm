mkdir /mnt/cluster/data/ANTPD/bids2
cd /mnt/cluster/data/ANTPD/bids2
# aws s3 sync --no-sign-request s3://openneuro.org/ds001907 . --exclude 'derivatives/*'
openneuro download --snapshot 2.0.3 ds001907 .

