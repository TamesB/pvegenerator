# Generated by Django 3.0.8 on 2020-11-13 15:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("project", "0023_auto_20201112_1731"),
    ]

    operations = [
        migrations.AddField(
            model_name="pveitemannotation",
            name="bijlage",
            field=models.BooleanField(blank=True, default=False, null=True),
        ),
    ]
