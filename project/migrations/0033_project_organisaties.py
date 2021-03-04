# Generated by Django 3.0.8 on 2021-01-21 15:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0014_auto_20210121_1657"),
        ("project", "0032_auto_20201201_1626"),
    ]

    operations = [
        migrations.AddField(
            model_name="project",
            name="organisaties",
            field=models.ManyToManyField(
                blank=True,
                default=None,
                null=True,
                related_name="organisaties",
                to="users.Organisatie",
            ),
        ),
    ]
