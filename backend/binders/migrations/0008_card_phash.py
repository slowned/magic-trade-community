"""Add phash field to Card for perceptual-hash-based scanner matching."""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('binders', '0007_merge_20260603_2048'),
    ]

    operations = [
        migrations.AddField(
            model_name='card',
            name='phash',
            field=models.CharField(blank=True, default='', max_length=16),
        ),
    ]
