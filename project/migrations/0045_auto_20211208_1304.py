# Generated by Django 3.1.12 on 2021-12-08 12:04

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('project', '0044_pveitemannotation_firststatus'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='pveitemannotation',
            options={'ordering': ['-date']},
        ),
        migrations.RenameField(
            model_name='beheerdersuitnodiging',
            old_name='klantenorganisatie',
            new_name='client',
        ),
        migrations.RenameField(
            model_name='beleggers',
            old_name='naam',
            new_name='name',
        ),
        migrations.RenameField(
            model_name='beleggers',
            old_name='abbonement',
            new_name='subscription',
        ),
        migrations.RenameField(
            model_name='bijlagetoannotation',
            old_name='bijlage',
            new_name='attachment',
        ),
        migrations.RenameField(
            model_name='bijlagetoannotation',
            old_name='naam',
            new_name='name',
        ),
        migrations.RenameField(
            model_name='project',
            old_name='belegger',
            new_name='client',
        ),
        migrations.RenameField(
            model_name='project',
            old_name='datum_aangemaakt',
            new_name='date_aangemaakt',
        ),
        migrations.RenameField(
            model_name='project',
            old_name='datum_recent_verandering',
            new_name='date_recent_verandering',
        ),
        migrations.RenameField(
            model_name='project',
            old_name='naam',
            new_name='name',
        ),
        migrations.RenameField(
            model_name='pveitemannotation',
            old_name='bijlage',
            new_name='attachment',
        ),
        migrations.RenameField(
            model_name='pveitemannotation',
            old_name='kostenConsequenties',
            new_name='consequentCosts',
        ),
        migrations.RenameField(
            model_name='pveitemannotation',
            old_name='datum',
            new_name='date',
        ),
        migrations.RenameField(
            model_name='pveitemannotation',
            old_name='gebruiker',
            new_name='user',
        ),
        migrations.AddField(
            model_name='pveitemannotation',
            name='costs_per_unit',
            field=models.BooleanField(blank=True, default=False, null=True),
        ),
        migrations.AlterField(
            model_name='bijlagetoannotation',
            name='ann',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, related_name='attachmentobject', to='project.pveitemannotation'),
        ),
    ]
