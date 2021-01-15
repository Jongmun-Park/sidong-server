from django.db import models
from django.contrib.postgres.fields import ArrayField
from phonenumber_field.modelfields import PhoneNumberField
from file.models import File


class Artist(models.Model):
    PAINTER = 0
    SCULPTOR = 1
    CRAFTSMAN = 2
    ETC = 3

    CHOICES_OF_CATEGORY = (
        (PAINTER, '화가'),
        (SCULPTOR, '조각가'),
        (CRAFTSMAN, '공예가'),
        (ETC, '기타'),
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    artist_name = models.CharField(max_length=32)
    real_name = models.CharField(max_length=32)
    phone = PhoneNumberField(null=True)
    description = models.TextField(blank=True)
    thumbnail = models.ForeignKey(File, null=True, on_delete=models.SET_NULL)
    category = models.IntegerField(
        choices=CHOICES_OF_CATEGORY, default=PAINTER)
