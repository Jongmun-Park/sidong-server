# from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.contrib.auth.models import User
from phonenumber_field.modelfields import PhoneNumberField
from file.models import File


class Artist(models.Model):
    PAINTER = 0
    SCULPTOR = 1
    CRAFTSMAN = 2
    ETC = 3

    CHOICES_OF_CATEGORY = [
        (PAINTER, '화가'),
        (SCULPTOR, '조각가'),
        (CRAFTSMAN, '공예가'),
        (ETC, '기타'),
    ]

    SEOUL = 0
    PUSAN = 1
    DAEGU = 2
    INCHEON = 3
    GWANGJU = 4
    DAEJEON = 5
    ULSAN = 6
    SEJONG = 7
    GYEONGGI = 8
    GANGWON = 9
    CHUNGBUK = 10
    CHUNGNAM = 11
    JEONBUK = 12
    JEONNAM = 13
    GYEONGBUK = 14
    GYEONGNAM = 15
    JEJU = 16

    CHOICES_OF_RESIDENCE = [
        (SEOUL, '서울특별시'),
        (PUSAN, '부산광역시'),
        (DAEGU, '대구광역시'),
        (INCHEON, '인천광역시'),
        (GWANGJU, '광주광역시'),
        (DAEJEON, '대전광역시'),
        (ULSAN, '울산광역시'),
        (SEJONG, '세종특별자치시'),
        (GYEONGGI, '경기도'),
        (GANGWON, '강원도'),
        (CHUNGBUK, '충청북도'),
        (CHUNGNAM, '충청남도'),
        (JEONBUK, '전라북도'),
        (JEONNAM, '전라남도'),
        (GYEONGBUK, '경상북도'),
        (GYEONGNAM, '경상남도'),
        (JEJU, '제주특별자치도'),
    ]

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='artist')
    is_approved = models.BooleanField(default=False)
    artist_name = models.CharField(max_length=32)
    real_name = models.CharField(max_length=32)
    phone = PhoneNumberField(null=True)
    description = models.TextField(blank=True)
    thumbnail = models.ForeignKey(
        File, null=True, on_delete=models.SET_NULL, related_name='artist_of_thumbnail')
    representative_work = models.ForeignKey(
        File, null=True, on_delete=models.SET_NULL, related_name='artist_of_representative_work')
    category = models.PositiveIntegerField(
        choices=CHOICES_OF_CATEGORY, default=PAINTER)
    residence = models.PositiveIntegerField(
        choices=CHOICES_OF_RESIDENCE, default=SEOUL)
