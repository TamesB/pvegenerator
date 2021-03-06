# Generated by Django 3.0.8 on 2020-09-16 21:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0005_auto_20200913_1749"),
    ]

    operations = [
        migrations.AddField(
            model_name="customuser",
            name="afdeling",
            field=models.CharField(blank=True, default=None, max_length=500, null=True),
        ),
        migrations.AddField(
            model_name="customuser",
            name="functie",
            field=models.CharField(blank=True, default=None, max_length=500, null=True),
        ),
        migrations.AddField(
            model_name="invitation",
            name="user_afdeling",
            field=models.CharField(blank=True, default=None, max_length=500, null=True),
        ),
        migrations.AddField(
            model_name="invitation",
            name="user_functie",
            field=models.CharField(blank=True, default=None, max_length=500, null=True),
        ),
    ]
