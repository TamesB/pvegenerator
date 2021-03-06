# Generated by Django 3.0.8 on 2020-09-13 16:44

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("project", "0011_project_belegger"),
    ]

    operations = [
        migrations.AddField(
            model_name="project",
            name="projectmanager",
            field=models.ForeignKey(
                default=None,
                on_delete=django.db.models.deletion.CASCADE,
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="project",
            name="permitted",
            field=models.ManyToManyField(
                default=None, related_name="permitted", to=settings.AUTH_USER_MODEL
            ),
        ),
    ]
