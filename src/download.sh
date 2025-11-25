mkdir -p ./data/ANTPD/bids
cd ./data/ANTPD/bids
aws s3 sync --no-sign-request s3://openneuro.org/ds001907 . \
  --exclude "derivatives/*" \
  --exclude "*task*"
