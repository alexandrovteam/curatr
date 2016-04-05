# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-02-08 17:06
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('standards_review', '0026_auto_20160208_1703'),
    ]

    operations = [
        migrations.AddField(
            model_name='inventory',
            name='location',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='inventory',
            name='standard',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE,
                                    to='standards_review.Standard'),
        ),
    ]