# Generated by Django 4.0.1 on 2022-02-02 08:37

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('project', '0048_remove_beleggers_beheerder_and_more'),
        ('app', '0026_auto_20211208_1335'),
    ]

    operations = [
        migrations.AlterField(
            model_name='actieveversie',
            name='client',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='actieve_versie', to='project.client'),
        ),
        migrations.AlterField(
            model_name='pveversie',
            name='client',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='version', to='project.client'),
        ),
    ]
