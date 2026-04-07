import pytest
import boto3
from moto import mock_aws
from io import BytesIO
from unittest.mock import patch
import os
from services.aws import upload_file, delete_file, generate_presigned_url, upload_submission, upload_assignment_file




os.environ["AWS_ACCESS_KEY_ID"] = "testing"
os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
os.environ["AWS_REGION"] = "us-east-2"
os.environ["AWS_BUCKET_NAME"] = "project-canvas-ai-bucket"



@pytest.fixture
def s3_bucket():
    with mock_aws():
        client = boto3.client("s3", region_name="us-east-2")
        client.create_bucket(
            Bucket="project-canvas-ai-bucket",
            CreateBucketConfiguration={"LocationConstraint": "us-east-2"}
        )
        yield client


def test_upload_file(s3_bucket):
    file = BytesIO(b"hello world")
    key = upload_file(file, "test/file.txt")
    assert key == "test/file.txt"


def test_upload_file_returns_key(s3_bucket):
    file = BytesIO(b"some content")
    key = upload_file(file, "submissions/123/456/hw.pdf")
    assert key == "submissions/123/456/hw.pdf"


def test_delete_file(s3_bucket):
    file = BytesIO(b"hello")
    upload_file(file, "test/delete_me.txt")
    result = delete_file("test/delete_me.txt")
    assert result == True


def test_delete_file_not_found(s3_bucket):
    result = delete_file("nonexistent/file.txt")
    assert result == True


def test_generate_presigned_url(s3_bucket):
    file = BytesIO(b"hello")
    upload_file(file, "test/file.txt")

    url = generate_presigned_url("test/file.txt")
    assert url is not None
    assert "test/file.txt" in url
    assert "X-Amz-Signature" in url


def test_generate_presigned_url_custom_expiry(s3_bucket):
    file = BytesIO(b"hello")
    upload_file(file, "test/file.txt")
    url = generate_presigned_url("test/file.txt", expires_in=7200)
    assert url is not None


def test_upload_submission(s3_bucket):
    file = BytesIO(b"my answer")
    assignment_id = "aaa-111"
    user_id = "bbb-222"
    filename = "submission.pdf"
    key = upload_submission(file, assignment_id, user_id, filename)
    assert key == f"submissions/{assignment_id}/{user_id}/{filename}"


def test_upload_assignment_file(s3_bucket):
    file = BytesIO(b"assignment content")
    class_id = "ccc-333"
    assignment_id = "aaa-111"
    filename = "hw1.pdf"
    key = upload_assignment_file(file, class_id, assignment_id, filename)
    assert key == f"assignments/{class_id}/{assignment_id}/{filename}"


def test_upload_file_bad_input(s3_bucket):
    result = upload_file(None, "test/file.txt")
    assert result is None