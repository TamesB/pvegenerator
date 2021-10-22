# Generated by Django 3.1.12 on 2021-10-20 10:29

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('project', '0041_auto_20211014_1451'),
        ('app', '0020_pveversie_public'),
    ]

    operations = [
        migrations.AlterField(
            model_name='actieveversie',
            name='belegger',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='actieve_versie', to='project.beleggers'),
        ),
        migrations.AlterField(
            model_name='pveversie',
            name='belegger',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='versie', to='project.beleggers'),
        ),
    ]