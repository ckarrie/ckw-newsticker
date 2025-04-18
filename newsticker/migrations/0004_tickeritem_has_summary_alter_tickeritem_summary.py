# Generated by Django 5.1.2 on 2025-04-03 08:51

import djangocms_text_ckeditor.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('newsticker', '0003_alter_tickeritemtype_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='tickeritem',
            name='has_summary',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='tickeritem',
            name='summary',
            field=djangocms_text_ckeditor.fields.HTMLField(blank=True, help_text='Cited Work: GRÜNEN | Marker: Referenz', null=True),
        ),
    ]
