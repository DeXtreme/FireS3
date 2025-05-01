import pytest
from io import BytesIO
from fires3.infrastructure.repositories import FakeS3Resource
from fires3.infrastructure.repositories import S3Bucket



@pytest.fixture
def s3_bucket():
    resource = FakeS3Resource("object_1","object_2")
    bucket = S3Bucket("test_bucket", s3_resource=resource)

    return bucket

def test_s3_bucket_list(s3_bucket):
    objects = s3_bucket.list()
    assert len(objects) == 2

def test_s3_bucket_get(s3_bucket):
    object = s3_bucket.get("object_1")
    assert object.key == "object_1"

def test_s3_bucket_create(s3_bucket):
    object = s3_bucket.create("object_3",BytesIO(b"object_3"))
    assert object.key == "object_3"

def test_s3_bucket_delete(s3_bucket):
    deleted = s3_bucket.delete("object_2")
    assert deleted