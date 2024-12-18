# Generated by Django 3.0.8 on 2020-12-01 13:21

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0010_auto_20200929_1626"),
    ]

    operations = [
        migrations.AlterField(
            model_name="customuser",
            name="type_user",
            field=models.CharField(
                choices=[
                    ("B", "Beheerder"),
                    ("SB", "PVETool Beheerder"),
                    ("SOG", "PVETool Projectmanager"),
                    ("SD", "PVETool Derden"),
                    ("SOC", "PVETool Opmerkingchecker"),
                ],
                default="SD",
                max_length=3,
            ),
        ),
        migrations.CreateModel(
            name="CommentCheckInvitation",
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
                (
                    "user_functie",
                    models.CharField(
                        blank=True, default=None, max_length=500, null=True
                    ),
                ),
                (
                    "user_afdeling",
                    models.CharField(
                        blank=True, default=None, max_length=500, null=True
                    ),
                ),
                ("expires", models.DateTimeField()),
                ("key", models.CharField(max_length=100)),
                (
                    "inviter",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
    ]
