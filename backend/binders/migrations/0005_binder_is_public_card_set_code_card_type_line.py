from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('binders', '0004_bindercard_etched_bindercard_foil_card_price_usd_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='binder',
            name='is_public',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='card',
            name='set_code',
            field=models.CharField(blank=True, default='', max_length=10),
        ),
        migrations.AddField(
            model_name='card',
            name='type_line',
            field=models.CharField(blank=True, default='', max_length=255),
        ),
        migrations.AlterField(
            model_name='card',
            name='uri',
            field=models.CharField(max_length=512),
        ),
        migrations.AlterField(
            model_name='card',
            name='scryfall_uri',
            field=models.CharField(max_length=512),
        ),
        migrations.AlterField(
            model_name='card',
            name='image_uri',
            field=models.URLField(blank=True, default='', max_length=512),
        ),
    ]
