# Generated by Django 4.0.1 on 2022-02-02 08:48

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('project', '0050_alter_client_beheerder_alter_client_subscription'),
    ]

    operations = [
        migrations.AlterField(
            model_name='beheerdersuitnodiging',
            name='client',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='pending_invitation', to='project.client'),
        ),
    ]
