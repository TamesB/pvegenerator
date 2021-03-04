# Generated by Django 3.0.8 on 2020-10-01 16:12

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("project", "0014_auto_20200929_1725"),
        ("syntrus", "0003_room"),
    ]

    operations = [
        migrations.AddField(
            model_name="room",
            name="project",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="project.Project",
            ),
        ),
    ]
