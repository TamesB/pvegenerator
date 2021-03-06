# Generated by Django 3.0.8 on 2020-09-13 15:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0004_invitation"),
    ]

    operations = [
        migrations.AlterField(
            model_name="customuser",
            name="type_user",
            field=models.CharField(
                choices=[
                    ("B", "Beheerder"),
                    ("SB", "Syntrus Beheerder"),
                    ("SOG", "Syntrus Projectmanager"),
                    ("SD", "Syntrus Derden"),
                ],
                default="SD",
                max_length=3,
            ),
        ),
    ]
