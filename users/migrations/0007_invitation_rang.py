# Generated by Django 3.0.8 on 2020-09-29 13:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0006_auto_20200916_2318'),
    ]

    operations = [
        migrations.AddField(
            model_name='invitation',
            name='rang',
            field=models.CharField(default=None, max_length=100, null=True),
        ),
    ]