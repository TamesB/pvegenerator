# Generated by Django 3.1.12 on 2021-10-20 10:29

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0023_auto_20211015_1408'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customuser',
            name='organisatie',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='user', to='users.organisatie'),
        ),
    ]
