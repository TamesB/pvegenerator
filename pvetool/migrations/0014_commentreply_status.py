# Generated by Django 3.0.8 on 2021-02-06 14:30

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("pvetool", "0013_frozencomments_todo_comments"),
    ]

    operations = [
        migrations.AddField(
            model_name="commentreply",
            name="status",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="pvetool.CommentStatus",
            ),
        ),
    ]