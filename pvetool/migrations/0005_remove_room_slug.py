# Generated by Django 3.0.8 on 2020-10-01 16:16

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("pvetool", "0004_room_project"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="room",
            name="slug",
        ),
    ]
