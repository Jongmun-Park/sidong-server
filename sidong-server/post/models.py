from django.db import models


class Post(models.Model):
    title = models.CharField(max_length=256)
    # thumbnail = models.ImageField(upload_to='art/thumbnails')

    def __str__(self):
        return self.title
