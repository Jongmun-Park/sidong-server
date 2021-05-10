from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone
import boto3
from botocore.exceptions import ClientError


class File(models.Model):
    BUCKET_ASSETS = "assets"

    CHOICES_OF_BUCKET = [
        (BUCKET_ASSETS, "기본 버킷"),
    ]

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    name = models.CharField(max_length=128, null=True)
    bucket = models.CharField(
        max_length=8, choices=CHOICES_OF_BUCKET, default=BUCKET_ASSETS)
    path = models.CharField(max_length=256)
    content_type = models.CharField(max_length=32)
    user = models.ForeignKey(
        User, null=True, on_delete=models.SET_NULL, related_name='files')

    @property
    def url(self):
        return "https://s3.ap-northeast-2.amazonaws.com/" + self.bucket + \
            ".storage.jakupsil.co.kr/" + self.path


def get_file_path(file):
    current_time = timezone.now()
    return current_time.strftime("%Y") + "/" + current_time.strftime(
        "%m") + "/" + current_time.strftime("%d") + "/" + current_time.strftime("%H%M%s") + file.name


def upload_file(file, file_path, bucket):
    bucket += ".storage.jakupsil.co.kr"
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
    except ClientError as error:
        return {'status': 'fail', msg: error.msg}

    return {'status': 'success'}


def create_file(file, bucket, user):
    file_path = get_file_path(file)
    result_of_upload_to_s3 = upload_file(file, file_path, bucket)

    if result_of_upload_to_s3['status'] == 'fail':
        return {
            'status': 'fail',
            'msg': result_of_upload_to_s3['msg'],
        }

    try:
        instance = File.objects.create(
            name=file.name,
            bucket=bucket,
            path=file_path,
            content_type=file.content_type,
            user=user,
        )
        return {
            'status': 'success',
            'instance': instance,
        }
    except Exception as error:
        return {
            'status': 'fail',
            'msg': error,
        }


def validate_file(file, bucket):
    file_name = file.name

    if file.size > 10000000:
        return {
            'status': 'fail',
            'msg': '파일 용량은 10MB까지 가능합니다. ' + file_name + ' 용량을 확인해주세요.',
        }

    file_path = get_file_path(file)

    if File.objects.filter(bucket=bucket, path=file_path).exists():
        return {
            'status': 'fail',
            'msg': '이미 존재하는 파일명입니다. ' + file_name + '의 이름을 변경해주세요.'
        }

    return {'status': 'success'}
