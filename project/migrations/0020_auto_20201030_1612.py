# Generated by Django 3.0.8 on 2020-10-30 15:12

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import functools
import utils.upload_rename


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('app', '0008_auto_20200922_1546'),
        ('project', '0019_auto_20201008_1800'),
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
                ('annbijlage', models.FileField(blank=True, null=True, upload_to=functools.partial(utils.upload_rename._update_filename, *(), **{'path': 'OpmerkingBijlages'}))),
                ('gebruiker', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('item', models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, to='app.PVEItem')),
                ('project', models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, to='project.Project')),
            ],
        ),
    ]