# Generated by Django 3.0.8 on 2020-09-02 11:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0002_auto_20200723_2330'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pveitem',
            name='bijlage',
            field=models.FileField(blank=True, null=True, upload_to='attachments'),
        ),
    ]