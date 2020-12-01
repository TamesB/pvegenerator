# Generated by Django 3.0.8 on 2020-12-01 15:26

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0010_auto_20201116_1701'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('project', '0031_auto_20201201_1623'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project',
            name='bouwsoort1',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='app.Bouwsoort'),
        ),
        migrations.AlterField(
            model_name='project',
            name='bouwsoort2',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='SubBouwsoort', to='app.Bouwsoort'),
        ),
        migrations.AlterField(
            model_name='project',
            name='bouwsoort3',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='SubSubBouwsoort', to='app.Bouwsoort'),
        ),
        migrations.AlterField(
            model_name='project',
            name='commentchecker',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='commentchecker', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='project',
            name='doelgroep1',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='app.Doelgroep'),
        ),
        migrations.AlterField(
            model_name='project',
            name='doelgroep2',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='SubDoelgroep', to='app.Doelgroep'),
        ),
        migrations.AlterField(
            model_name='project',
            name='doelgroep3',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='SubSubDoelgroep', to='app.Doelgroep'),
        ),
        migrations.AlterField(
            model_name='project',
            name='projectmanager',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='project',
            name='typeObject1',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='app.TypeObject'),
        ),
        migrations.AlterField(
            model_name='project',
            name='typeObject2',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='SubTypeObject', to='app.TypeObject'),
        ),
        migrations.AlterField(
            model_name='project',
            name='typeObject3',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='SubSubTypeObject', to='app.TypeObject'),
        ),
    ]
