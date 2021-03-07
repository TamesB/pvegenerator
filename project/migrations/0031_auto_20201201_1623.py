# Generated by Django 3.0.8 on 2020-12-01 15:23

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("project", "0030_auto_20201201_1530"),
    ]

    operations = [
        migrations.AlterField(
            model_name="project",
            name="commentchecker",
            field=models.ForeignKey(
                default=None,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="commentchecker",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
