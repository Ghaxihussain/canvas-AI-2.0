from dotenv import load_dotenv
import os
import boto3

load_dotenv()


s3 = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION")
)

s3.upload_file("test.txt", os.getenv("AWS_BUCKET_NAME"), "test/test.txt")