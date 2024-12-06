# Generated by Django 4.0.1 on 2022-02-16 12:33

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0029_logindetails'),
    ]

    operations = [
        migrations.AddField(
            model_name='logindetails',
            name='device_type',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name='logindetails',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='login_details', to=settings.AUTH_USER_MODEL),
        ),
    ]
