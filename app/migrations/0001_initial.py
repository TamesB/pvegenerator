# Generated by Django 2.2.7 on 2020-03-25 11:51

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='PVEInhoudOnderdeel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('naam', models.CharField(max_length=256)),
            ],
        ),
        migrations.CreateModel(
            name='PVEOnderdeel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('naam', models.CharField(max_length=256)),
            ],
        ),
        migrations.CreateModel(
            name='PVEParameters',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('parameter', models.CharField(max_length=256)),
            ],
        ),
        migrations.CreateModel(
            name='PVESectie',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('hoofdstuk', models.IntegerField()),
                ('paragraaf', models.IntegerField()),
                ('subparagraaf', models.IntegerField()),
                ('STABUhoofdstuk', models.IntegerField()),
                ('STABUnaam', models.CharField(max_length=256)),
                ('STABUparagraaf', models.CharField(max_length=256)),
            ],
        ),
        migrations.CreateModel(
            name='PVEItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('inhoud', models.CharField(max_length=5000)),
                ('bijlage', models.FileField(upload_to='')),
                ('inhoudonderdeel', models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='app.PVEInhoudOnderdeel')),
                ('onderdeel', models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='app.PVEOnderdeel')),
                ('parameters', models.ManyToManyField(to='app.PVEParameters')),
                ('sectie', models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='app.PVESectie')),
            ],
        ),
    ]
