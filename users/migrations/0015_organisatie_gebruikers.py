# Generated by Django 3.0.8 on 2021-01-21 16:48

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0014_auto_20210121_1657'),
    ]

    operations = [
        migrations.AddField(
            model_name='organisatie',
            name='gebruikers',
            field=models.ManyToManyField(default=None, related_name='gebruikers', to=settings.AUTH_USER_MODEL),
        ),
    ]