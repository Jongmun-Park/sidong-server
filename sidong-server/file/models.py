from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone
import boto3
from botocore.exceptions import ClientError


class File(models.Model):
    BUCKET_ASSETS = "assets"

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    name = models.CharField(max_length=64, null=True)
    bucket = models.CharField(max_length=64, choices=[(BUCKET_ASSETS, "게시글")])
    path = models.CharField(max_length=256)
    content_type = models.CharField(max_length=128)
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)

    def create_file(file, bucket):
        # 오늘 날짜에 생성된 데이터 중 파일명 중복 체크해야 함.
        file_path = timezone.now().strftime("%Y%m%d") + "/" + file.name

        upload_file(file, file_path, bucket)
        pass

    @staticmethod
    def upload_file(file, file_path, bucket="assets.storage.jakupsil.co.kr"):
        s3_client = boto3.client(
            service_name="s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name="ap-northeast-2",
        )

        try:
            s3_client.put_object(
                Key=file_path,
                ACL="public-read",
                Body=file,
                Bucket=bucket,
                ContentType=file.content_type,
            )
        except ClientError as e:
            return False

        return True
