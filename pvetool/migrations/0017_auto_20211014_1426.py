# Generated by Django 3.1.12 on 2021-10-14 12:26

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('project', '0040_auto_20211014_1426'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('pvetool', '0016_bijlagetoreply_naam'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='commentreply',
            options={'ordering': ['-datum']},
        ),
        migrations.AlterModelOptions(
            name='frozencomments',
            options={'ordering': ['-level']},
        ),
        migrations.AlterField(
            model_name='bijlagetoreply',
            name='reply',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, related_name='bijlagetoreply', to='pvetool.commentreply'),
        ),
        migrations.AlterField(
            model_name='commentreply',
            name='commentphase',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='reply', to='pvetool.frozencomments'),
        ),
        migrations.AlterField(
            model_name='commentreply',
            name='gebruiker',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='reply', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='commentreply',
            name='onComment',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='reply', to='project.pveitemannotation'),
        ),
        migrations.AlterField(
            model_name='commentreply',
            name='status',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='reply', to='pvetool.commentstatus'),
        ),
        migrations.AlterField(
            model_name='frozencomments',
            name='accepted_comments',
            field=models.ManyToManyField(related_name='phase_accept', to='project.PVEItemAnnotation'),
        ),
        migrations.AlterField(
            model_name='frozencomments',
            name='comments',
            field=models.ManyToManyField(related_name='phase_comments', to='project.PVEItemAnnotation'),
        ),
        migrations.AlterField(
            model_name='frozencomments',
            name='project',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='phase', to='project.project'),
        ),
        migrations.AlterField(
            model_name='frozencomments',
            name='todo_comments',
            field=models.ManyToManyField(related_name='phase_todo', to='project.PVEItemAnnotation'),
        ),
    ]
