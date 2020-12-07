# Generated by Django 3.0.8 on 2020-12-01 14:29

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('project', '0028_project_commentchecker'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project',
            name='commentchecker',
            field=models.ForeignKey(default=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='commentchecker', to=settings.AUTH_USER_MODEL),
        ),
    ]