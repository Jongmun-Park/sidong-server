from django.db import models
from phonenumber_field.modelfields import PhoneNumberField


class Artist(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    artist_name = models.CharField(max_length=64)
    real_name = models.CharField(max_length=32)
    phone = PhoneNumberField(null=True)
    description = models.TextField(blank=True)
    # thumbnail =
    # categories =
