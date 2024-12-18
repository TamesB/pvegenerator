# Generated by Django 4.0.1 on 2022-02-02 08:37

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('project', '0048_remove_beleggers_beheerder_and_more'),
        ('users', '0027_auto_20211208_1304'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customuser',
            name='client',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='employee', to='project.client'),
        ),
        migrations.AlterField(
            model_name='invitation',
            name='client',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='project.client'),
        ),
        migrations.AlterField(
            model_name='organisatie',
            name='client',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='stakeholder', to='project.client'),
        ),
    ]
