# Generated by Django 3.1.7 on 2021-08-11 14:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0017_itembijlages_naam'),
    ]

    operations = [
        migrations.AlterField(
            model_name='itembijlages',
            name='items',
            field=models.ManyToManyField(blank=True, to='app.PVEItem'),
        ),
    ]
