# Generated by Django 3.0.8 on 2020-11-16 16:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0009_auto_20201103_1437'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pveitem',
            name='bijlage',
            field=models.FileField(blank=True, null=True, upload_to='BasisBijlages'),
        ),
    ]
