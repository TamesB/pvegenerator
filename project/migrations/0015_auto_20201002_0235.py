# Generated by Django 3.0.8 on 2020-10-02 00:35

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0008_auto_20200922_1546'),
        ('project', '0014_auto_20200929_1725'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='bouwsoort3',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='SubSubBouwsoort', to='app.Bouwsoort'),
        ),
        migrations.AddField(
            model_name='project',
            name='doelgroep3',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='SubSubDoelgroep', to='app.Doelgroep'),
        ),
        migrations.AddField(
            model_name='project',
            name='typeObject3',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='SubSubTypeObject', to='app.TypeObject'),
        ),
    ]