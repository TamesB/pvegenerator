# Generated by Django 3.0.8 on 2020-07-24 13:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("project", "0003_project_plaatsnamen"),
    ]

    operations = [
        migrations.AlterField(
            model_name="project",
            name="plaatsnamen",
            field=models.CharField(default=None, max_length=250, null=True),
        ),
    ]
