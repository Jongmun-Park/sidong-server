from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=16)

    def __str__(self):
        return self.name


class Art(models.Model):
    name = models.CharField(max_length=128)
    category = models.ForeignKey(
        Category, related_name="arts", null=True, on_delete=models.SET_NULL
    )

    def __str__(self):
        return self.name
