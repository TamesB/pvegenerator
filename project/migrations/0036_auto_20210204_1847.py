# Generated by Django 3.0.8 on 2021-02-04 17:47

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("syntrus", "0011_commentreply_accept"),
        ("project", "0035_pveitemannotation_init_accepted"),
    ]

    operations = [
        migrations.AlterField(
            model_name="pveitemannotation",
            name="status",
            field=models.ForeignKey(
                default=None,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="syntrus.CommentStatus",
            ),
        ),
    ]
