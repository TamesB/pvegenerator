# Generated by Django 2.2.7 on 2020-03-25 13:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0005_auto_20200325_1422'),
    ]

    operations = [
        migrations.AlterField(
            model_name='stabuhoofdstuk',
            name='hoofdstukSTABU',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
