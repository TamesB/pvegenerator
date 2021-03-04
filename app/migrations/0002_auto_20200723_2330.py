# Generated by Django 3.0.8 on 2020-07-23 21:30

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("project", "0001_initial"),
        ("app", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="pveitem",
            name="projects",
            field=models.ManyToManyField(blank=True, to="project.Project"),
        ),
        migrations.AddField(
            model_name="pvehoofdstuk",
            name="onderdeel",
            field=models.ForeignKey(
                default=1,
                on_delete=django.db.models.deletion.CASCADE,
                to="app.PVEOnderdeel",
            ),
        ),
    ]
