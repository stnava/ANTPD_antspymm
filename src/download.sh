mkdir /mnt/cluster/data/ANTPD/bids
cd /mnt/cluster/data/ANTPD/bids
aws s3 sync --no-sign-request s3://openneuro.org/ds001907 . --exclude 'derivatives/*'

