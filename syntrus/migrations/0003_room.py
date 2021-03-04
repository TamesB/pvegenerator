# Generated by Django 3.0.8 on 2020-10-01 16:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("syntrus", "0002_faq_gebruikersrang"),
    ]

    operations = [
        migrations.CreateModel(
            name="Room",
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
                ("name", models.CharField(max_length=30)),
                ("description", models.CharField(max_length=100)),
                ("slug", models.CharField(max_length=50)),
            ],
        ),
    ]
