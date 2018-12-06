import os
import boto3
import pandas as pd
from urllib.request import urlopen
from time import sleep


def get_contract_codes():
    cme_metadata = pd.read_csv('/code/data/CME_metadata.csv')
    cme_futures = pd.read_csv('/code/data/CME_futures.csv')

    futures_codes = cme_futures['Futures Symbol'].tolist()
    contract_codes = []

    for futures_code in futures_codes:
        length = (cme_metadata['code'].str.len() == len(futures_code) + 5)
        starts_with = cme_metadata['code'].str.startswith(futures_code)
        results = cme_metadata[length & starts_with]['code'].tolist()
        contract_codes.extend(results)

    return contract_codes


def upload_quandl_contract_to_s3(exchange_code, contract_code, boto_client):
    API_KEY = os.environ['QUANDL_API_KEY']

    if len(contract_code) == 6:
        futures_code = contract_code[0:1]
    elif len(contract_code) == 7:
        futures_code = contract_code[0:2]
    else:
        futures_code = contract_code[0:3]

    API_URL = f'http://www.quandl.com/api/v3/datasets/{exchange_code}/{contract_code}.csv' \
        f'?auth_token={API_KEY}&order=asc'

    FILENAME = f'data/raw_csv/futures/{futures_code}/daily/{contract_code}.csv'
    with urlopen(API_URL) as data:
        boto_client.upload_fileobj(data, 'financial-data-monitor', FILENAME)
    sleep(0.3)  # API Rate Limit is 300 calls per 10 seconds, 2000 calls per 10 minutes


if __name__== "__main__":
    s3 = boto3.client('s3')

    print('Uploading CME_metadata.csv to S3')
    s3.upload_file('/code/data/CME_metadata.csv',
                   'financial-data-monitor',
                   'data/CME_metadata.csv')

    print('Uploading CME_futures.csv to S3')
    s3.upload_file('/code/data/CME_futures.csv',
                   'financial-data-monitor',
                   'data/CME_futures.csv')

    contract_codes = get_contract_codes()
    for contract_code in contract_codes:
        print (f'Downloading {contract_code} and Uploading to S3')
        upload_quandl_contract_to_s3('CME', contract_code, s3)


