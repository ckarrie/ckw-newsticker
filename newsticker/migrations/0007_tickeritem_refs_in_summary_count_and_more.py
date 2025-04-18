# Generated by Django 5.1.2 on 2025-04-07 11:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('newsticker', '0006_tickerref_linked_tickeritem_alter_tickerref_item_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='tickeritem',
            name='refs_in_summary_count',
            field=models.IntegerField(default=0, editable=False),
        ),
        migrations.AddField(
            model_name='tickerref',
            name='is_in_summary',
            field=models.BooleanField(default=False, editable=False),
        ),
    ]
