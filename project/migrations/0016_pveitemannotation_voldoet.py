# Generated by Django 3.0.8 on 2020-10-05 11:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("project", "0015_auto_20201002_0235"),
    ]

    operations = [
        migrations.AddField(
            model_name="pveitemannotation",
            name="voldoet",
            field=models.BooleanField(blank=True, default=None, null=True),
        ),
    ]
