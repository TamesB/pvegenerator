# Generated by Django 3.0.8 on 2020-09-13 16:12

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('project', '0010_beleggers'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='belegger',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='project.Beleggers'),
        ),
    ]
