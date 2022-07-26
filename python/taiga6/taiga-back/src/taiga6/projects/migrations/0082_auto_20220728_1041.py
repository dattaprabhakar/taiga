# Generated by Django 3.2.13 on 2022-07-28 10:41

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('projects', '0081_remove_project_is_private'),
    ]

    operations = [
        migrations.AddField(
            model_name='invitation',
            name='resent_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='resent at'),
        ),
        migrations.AddField(
            model_name='invitation',
            name='resent_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='ihaveresent+', to=settings.AUTH_USER_MODEL),
        ),
    ]
