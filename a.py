import boto3

s3 = boto3.client(
    's3',
    aws_access_key_id='AKIAR7HWYD6HQQPRHVEX',
    aws_secret_access_key='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',
    region_name='eu-north-1'
)

# List buckets
response = s3.list_buckets()
print("Buckets:", [bucket['Name'] for bucket in response['Buckets']])

# Check if the bucket exists
try:
    s3.head_bucket(Bucket='vaibhavchat')
    print("Bucket exists and is accessible.")
except s3.exceptions.ClientError as e:
    print("Error:", e)
