# Generated by Django 3.0.8 on 2021-01-25 17:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('project', '0033_project_organisaties'),
    ]

    operations = [
        migrations.RenameField(
            model_name='project',
            old_name='datum',
            new_name='datum_aangemaakt',
        ),
        migrations.AddField(
            model_name='project',
            name='datum_recent_verandering',
            field=models.DateTimeField(auto_now=True, verbose_name='recente_verandering'),
        ),
    ]
