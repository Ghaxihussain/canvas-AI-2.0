import boto3
import os
from dotenv import load_dotenv

load_dotenv()

s3 = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION")
)

BUCKET = os.getenv("AWS_BUCKET_NAME")



# i will follow this structure:- submissions/{assignment_id}/{user_id}/{filename}
 
def upload_file(file, key: str):
    try:
        s3.upload_fileobj(file, BUCKET, key)
        return key
    except Exception as e:
        print(e)
        return None

def delete_file(key: str):
    try:
        s3.delete_object(Bucket=BUCKET, Key=key)
        return True
    except Exception as e:
        print(e)
        return False

def generate_presigned_url(key: str, expires_in: int = 3600):
    try:
        return s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": BUCKET, "Key": key},
            ExpiresIn=expires_in
        )
    except Exception as e:
        print(e)
        return None

def upload_submission(file, assignment_id, user_id, filename):
    key = f"submissions/{assignment_id}/{user_id}/{filename}"
    return upload_file(file, key)

def upload_assignment_file(file, class_id, assignment_id, filename):
    key = f"assignments/{class_id}/{assignment_id}/{filename}"
    return upload_file(file, key)



def get_s3_object(bucket: str, key: str) -> tuple[bytes, str]:
    response = s3.get_object(Bucket=bucket, Key=key)
    content = response["Body"].read()
    content_type = response["ContentType"]  
    return content, content_type