# Generated by Django 2.2.7 on 2020-03-26 14:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0008_auto_20200326_1549'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pveitem',
            name='AED',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='pveitem',
            name='EntreeUpgrade',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='pveitem',
            name='JamesConcept',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='pveitem',
            name='Pakketdient',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='pveitem',
            name='Smarthome',
            field=models.BooleanField(default=False),
        ),
    ]
