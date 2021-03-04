# Generated by Django 3.0.8 on 2020-07-23 21:30

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("project", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="project",
            name="permitted",
            field=models.ForeignKey(
                default=None,
                on_delete=django.db.models.deletion.CASCADE,
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="project",
            name="statuscontract",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="project.ContractStatus"
            ),
        ),
    ]
