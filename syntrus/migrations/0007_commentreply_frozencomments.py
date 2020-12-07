# Generated by Django 3.0.8 on 2020-12-07 19:35

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('project', '0032_auto_20201201_1626'),
        ('syntrus', '0006_commentstatus'),
    ]

    operations = [
        migrations.CreateModel(
            name='FrozenComments',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('level', models.IntegerField(blank=True, default=1, null=True)),
                ('comments', models.ManyToManyField(to='project.PVEItemAnnotation')),
                ('project', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='project.Project')),
            ],
        ),
        migrations.CreateModel(
            name='CommentReply',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('comment', models.TextField(default=None, max_length=1000, null=True)),
                ('commentphase', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='syntrus.FrozenComments')),
                ('onComment', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='project.PVEItemAnnotation')),
            ],
        ),
    ]