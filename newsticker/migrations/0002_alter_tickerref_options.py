# Generated by Django 5.1.2 on 2025-03-31 10:56

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('newsticker', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='tickerref',
            options={'ordering': ['item', 'index']},
        ),
    ]
