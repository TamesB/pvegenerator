# Generated by Django 3.0.8 on 2021-02-04 15:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("project", "0035_pveitemannotation_init_accepted"),
        ("syntrus", "0009_remove_frozencomments_open"),
    ]

    operations = [
        migrations.AddField(
            model_name="frozencomments",
            name="accepted_comments",
            field=models.ManyToManyField(
                related_name="accepted_comments", to="project.PVEItemAnnotation"
            ),
        ),
    ]
