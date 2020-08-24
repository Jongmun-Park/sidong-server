from django.db import models
import boto3
from botocore.exceptions import ClientError


class File(models.Model):
    BUCKET_POST = "s3_posts"

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    name = models.CharField(max_length=256, null=True)
    bucket = models.CharField(max_length=32, choices=((BUCKET_POST, "게시글"),))
    path = models.CharField(max_length=256)
    mime_type = models.CharField(max_length=128)
    # user_info = models.ForeignKey(
    #     UserInfo, null=True, on_delete=models.SET_NULL)
    # data = JSONField(null=True)

    def upload_file(
        file_name, bucket="assets.storage.jakupsil.co.kr", object_name=None
    ):
        """Upload a file to an S3 bucket
        :param file_name: File to upload
        :param bucket: Bucket to upload to
        :param object_name: S3 object name. If not specified then file_name is used
        :return: True if file was uploaded, else False
        """

        # If S3 object_name was not specified, use file_name
        if object_name is None:
            object_name = file_name

        # Upload the file
        s3_client = boto3.client("s3")
        try:
            response = s3_client.upload_file(file_name, bucket, object_name)
        except ClientError as e:
            print("upload_file error:", e)
            return False
        return True
