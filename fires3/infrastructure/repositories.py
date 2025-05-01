import logging
from io import BytesIO

import boto3
from botocore.exceptions import ClientError
from google.cloud import storage
from google.cloud.exceptions import GoogleCloudError

from ..domain.models import Object

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class S3BucketError(Exception):
    pass


class FakeS3Resource:
    class FakeBucket:
        class FakeObject:
            def __init__(self, key: str, fake_body=None, fake_bucket=None):
                self.key = key
                self.body = fake_body
                self._bucket = fake_bucket

            def get(self):
                if self.key in self._bucket._bucket_dict:
                    return {"Body": self._bucket._bucket_dict[self.key].body}

                raise ClientError({"Error": {"Code": "NoSuchKey"}}, operation_name="get")

            def delete(self):
                if self.key in self._bucket._bucket_dict:
                    del self._bucket._bucket_dict[self.key]
                    return True

                raise ClientError({"Error": {"Code": "NoSuchKey"}}, operation_name="delete")

            def upload_fileobj(self, obj):
                self.body = obj
                self._bucket._bucket_dict[self.key] = self

        class FakeObjectCollection:
            def __init__(self, fake_bucket=None):
                self._bucket = fake_bucket

            def all(self):
                return self._bucket._bucket_dict.values()

        def __init__(self, bucket: str, fake_keys: list):
            self.bucket = bucket
            self._bucket_dict = {}

            for fake_key in fake_keys:
                object = self.FakeObject(fake_key, fake_body=BytesIO(fake_key.encode()), fake_bucket=self)
                self._bucket_dict[fake_key] = object

            self.objects = self.FakeObjectCollection(fake_bucket=self)
        
        def Object(self,key: str):
            return self.FakeObject(key, fake_bucket=self)

    def __init__(self, *fake_keys):
        self.fake_keys = fake_keys
    
    def Bucket(self, bucket: str):
        return self. FakeBucket(bucket, self.fake_keys)

class S3Bucket:
    def __init__(self, bucket: str, s3_resource=None):
        if s3_resource:
            s3 = s3_resource
        else:
            s3 = boto3.resource("s3")
        self.bucket = bucket
        self._bucket = s3.Bucket(bucket)

    def list(self):
        try:
            bucket_objects = self._bucket.objects.all()

            objects = []
            for bucket_object in bucket_objects:
                logger.info(f"Listing {self.bucket}/{bucket_object.key}")
                body = self._bucket.Object(bucket_object.key).get()["Body"]
                objects.append(Object(bucket_object.key, body))

            return objects
        except ClientError as err:
            raise S3BucketError(
                f"Error occurred while listing objects in Bucket({self.bucket}): {err}"
            )

    def get(self, key: str) -> Object:
        try:
            logger.info(f"Getting {self.bucket}/{key}")
            body = self._bucket.Object(key).get()["Body"]
            return Object(key, body)
        except ClientError as err:
            raise S3BucketError(
                f"Error occurred while getting Object({key}) from Bucket({self.bucket}): {err}"
            )

    def create(self, key: str, content):
        try:
            logger.info(f"Creating {self.bucket}/{key}")
            self._bucket.Object(key).upload_fileobj(content)
            return self.get(key)
        except ClientError as err:
            raise S3BucketError(
                f"Error occurred creating Object({key}) in Bucket({self.bucket}): {err}"
            )

    def delete(self, key: str):
        try:
            logger.info(f"Deleting {self.bucket}/{key}")
            self._bucket.Object(key).delete()
            return True
        except ClientError as err:
            raise S3BucketError(
                f"Error occurred deleting Object({key}) from Bucket({self.bucket}): {err}"
            )


class GcpStorageError(Exception):
    pass


class GCPBucket:
    def __init__(self, bucket: str, storage_client=None):
        if storage_client:
            client = storage_client
        else:
            client = storage.Client()
        self.bucket = bucket
        self._bucket = client.bucket(bucket)

    def list(self):
        try:

            blobs = self._bucket.list_blobs()
            objects = []
            for blob in blobs:
                logger.info(f"Listing {self.bucket}/{blob.name}")
                objects.append(self.get(blob.name))
            return objects
        except GoogleCloudError as err:
            raise GcpStorageError(
                f"Error occurred while listing objects in Bucket({self.bucket}): {err}"
            )

    def get(self, key: str) -> Object:
        try:
            logger.info(f"Getting {self.bucket}/{key}")
            blob = self._bucket.blob(key)
            return Object(key, blob.open(mode="rb"))
        except GoogleCloudError as err:
            raise GcpStorageError(
                f"Error occurred while getting Object({key}) from Bucket({self.bucket}): {err}"
            )

    def create(self, key: str, content):
        try:
            logger.info(f"Creating {self.bucket}/{key}")
            blob = self._bucket.blob(key)
            blob.upload_from_file(content)
            return self.get(key)
        except GoogleCloudError as err:
            raise GcpStorageError(
                f"Error occurred creating Object({key}) in Bucket({self.bucket}): {err}"
            )

    def delete(self, key: str):
        try:
            logger.info(f"Deleting {self.bucket}/{key}")
            blob = self._bucket.blob(key)
            blob.delete()
            return True
        except GoogleCloudError as err:
            raise GcpStorageError(
                f"Error occurred deleting Object({key}) from Bucket({self.bucket}): {err}"
            )
