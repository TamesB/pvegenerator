# Generated by Django 3.0.8 on 2021-02-04 17:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('syntrus', '0010_frozencomments_accepted_comments'),
    ]

    operations = [
        migrations.AddField(
            model_name='commentreply',
            name='accept',
            field=models.BooleanField(blank=True, default=False, null=True),
        ),
    ]