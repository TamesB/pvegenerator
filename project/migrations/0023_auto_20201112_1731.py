# Generated by Django 3.0.8 on 2020-11-12 16:31

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('project', '0022_auto_20201103_1451'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='pveitemannotation',
            name='annbijlage',
        ),
        migrations.CreateModel(
            name='BijlageToAnnotation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('annbijlage', models.FileField(blank=True, null=True, upload_to='OpmerkingBijlages/')),
                ('ann', models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, to='project.PVEItemAnnotation')),
            ],
        ),
    ]
