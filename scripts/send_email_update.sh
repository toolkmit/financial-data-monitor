#!/usr/bin/env bash

echo "Getting CME Metadata from Quandl"
wget "https://www.quandl.com/api/v3/databases/CME/metadata?api_key=$QUANDL_API_KEY" -q -O CME_metadata.csv.zip
echo "Unpacking"
unzip -qq CME_metadata.csv.zip
rm CME_metadata.csv.zip
mv CME_metadata.csv data/CME_metadata.csv
echo "Finished Getting CME Metadata"
python fdmonitor/load_futures.py --update --s3
python fdmonitor/plotter.py --s3
python fdmonitor/emailer.py
echo "Finished....."