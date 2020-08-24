from django.db import models


class Post(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    title = models.CharField(max_length=256)
    # thumbnail = models.ImageField(upload_to='art/thumbnails')

    def __str__(self):
        return self.title
