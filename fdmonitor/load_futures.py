import boto3


if __name__== "__main__":
    s3 = boto3.client('s3')
    s3.upload_file('/code/data/CME_metadata.csv',
                   'financial-data-monitor',
                   'data/CME_metadata.csv')
