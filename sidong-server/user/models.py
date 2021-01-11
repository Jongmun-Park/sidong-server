from django.db import models
from django.contrib.postgres.fields import ArrayField
from phonenumber_field.modelfields import PhoneNumberField
from file.models import File


class Category(models.Model):
    name = models.CharField(max_length=64)


class Artist(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    artist_name = models.CharField(max_length=64)
    real_name = models.CharField(max_length=32)
    phone = PhoneNumberField(null=True)
    description = models.TextField(blank=True)
    thumbnail = models.ForeignKey(File, null=True, on_delete=models.SET_NULL)
    categories = ArrayField(models.CharField(max_length=64))
