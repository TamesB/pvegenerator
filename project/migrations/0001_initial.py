# Generated by Django 3.0.8 on 2020-07-23 21:30

import django.contrib.gis.db.models.fields
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("app", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ContractStatus",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("contrstatus", models.CharField(blank=True, max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name="Project",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("nummer", models.FloatField(default=None, max_length=100)),
                ("naam", models.CharField(default=None, max_length=500)),
                ("plaats", django.contrib.gis.db.models.fields.PointField(srid=4326)),
                ("vhe", models.FloatField(default=None, max_length=100)),
                ("pensioenfonds", models.CharField(default=None, max_length=100)),
                ("datum", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name="PVEItemAnnotation",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("annotation", models.TextField(default=None, max_length=1000)),
                (
                    "item",
                    models.ForeignKey(
                        default=None,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="app.PVEItem",
                    ),
                ),
                (
                    "project",
                    models.ForeignKey(
                        default=None,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="project.Project",
                    ),
                ),
            ],
        ),
    ]
