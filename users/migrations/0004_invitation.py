# Generated by Django 3.0.8 on 2020-09-11 15:34

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("project", "0009_auto_20200818_1734"),
        ("users", "0003_customuser_omschrijving"),
    ]

    operations = [
        migrations.CreateModel(
            name="Invitation",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("invitee", models.EmailField(max_length=254)),
                ("expires", models.DateTimeField()),
                ("key", models.CharField(max_length=100)),
                (
                    "inviter",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "project",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="project.Project",
                    ),
                ),
            ],
        ),
    ]
