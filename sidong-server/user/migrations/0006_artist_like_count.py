# Generated by Django 2.2.10 on 2021-04-02 03:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0005_auto_20210318_0913'),
    ]

    operations = [
        migrations.AddField(
            model_name='artist',
            name='like_count',
            field=models.PositiveIntegerField(default=0),
        ),
    ]