# Generated by Django 3.0.8 on 2020-10-01 15:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("pvetool", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="faq",
            name="gebruikersrang",
            field=models.CharField(
                choices=[
                    ("B", "Beheerder"),
                    ("SB", "PVETool Beheerder"),
                    ("SOG", "PVETool Projectmanager"),
                    ("SD", "PVETool Derden"),
                ],
                default="SD",
                max_length=3,
            ),
        ),
    ]
