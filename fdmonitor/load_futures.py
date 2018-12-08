import argparse
import pathlib
import os
import boto3
import pandas as pd
from urllib.request import urlopen, urlretrieve
from time import sleep
from datetime import date, timedelta


def get_contract_codes(is_update=False):
    """Generate list of contract codes to update/load"""

    cme_metadata = pd.read_csv('/code/data/CME_metadata.csv')
    cme_futures = pd.read_csv('/code/data/CME_futures.csv')

    futures_codes = cme_futures['Futures Symbol'].tolist()
    contract_codes = []

    for futures_code in futures_codes:
        length = (cme_metadata['code'].str.len() == len(futures_code) + 5)
        starts_with = cme_metadata['code'].str.startswith(futures_code)

        # If an update, we pull in futures that have been active in last 3 months
        if is_update:
            dt = (date.today() - timedelta(3 * 365 / 12)).isoformat()
        else:
            dt = '1900-01-01'
        date_filter = cme_metadata['to_date'] >= dt

        results = cme_metadata[length & starts_with & date_filter]['code'].tolist()
        contract_codes.extend(results)

    return contract_codes


def download_contract_from_quandl(exchange_code, contract_code, data_directory):
    """Download csvs from Quandl and store locally"""

    API_KEY = os.environ['QUANDL_API_KEY']
    API_URL = f'http://www.quandl.com/api/v3/datasets/{exchange_code}/{contract_code}.csv' \
        f'?auth_token={API_KEY}&order=asc'

    if len(contract_code) == 6:
        futures_code = contract_code[0:1]
    elif len(contract_code) == 7:
        futures_code = contract_code[0:2]
    else:
        futures_code = contract_code[0:3]
    CONTRACT_DATA_DIRNAME = data_directory / 'raw_csv' / 'futures' / f'{futures_code}' / 'daily'

    CONTRACT_DATA_DIRNAME.mkdir(parents=True, exist_ok=True)
    os.chdir(CONTRACT_DATA_DIRNAME)
    urlretrieve(API_URL, f'{contract_code}.csv')
    sleep(0.3)  # API Rate Limit is 300 calls per 10 seconds, 2000 calls per 10 minutes


def upload_quandl_contract_to_s3(exchange_code, contract_code, boto_client):
    """Download csvs from Quandl and store in S3"""

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
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--update",
        default=False,
        dest='update',
        action='store_true',
        help="Only update futures contracts that have been active in last 3mo"
    )
    parser.add_argument(
        "--s3",
        default=False,
        dest='s3',
        action='store_true',
        help="Store futures data in S3"
    )
    args = parser.parse_args()

    contract_codes = get_contract_codes(is_update=args.update)

    if args.s3:
        s3 = boto3.client('s3')

        print('Uploading CME_metadata.csv to S3')
        s3.upload_file('/code/data/CME_metadata.csv',
                       'financial-data-monitor',
                       'data/CME_metadata.csv')

        print('Uploading CME_futures.csv to S3')
        s3.upload_file('/code/data/CME_futures.csv',
                       'financial-data-monitor',
                       'data/CME_futures.csv')

        for contract_code in contract_codes:
            print (f'Downloading {contract_code} and Uploading to S3')
            upload_quandl_contract_to_s3('CME', contract_code, s3)
    else:
        DATA_DIRNAME = pathlib.Path('/code').resolve() / 'data'
        for contract_code in contract_codes:
            print (f'Downloading {contract_code}')
            download_contract_from_quandl('CME', contract_code, DATA_DIRNAME)


