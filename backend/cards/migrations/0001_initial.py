from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('binders', '0009_alter_wishlistcard_added_at'),
        # carts' pre-move migrations still create a real FK to 'binders.card';
        # they must run before Card is deleted from binders' state below.
        ('carts', '0004_remove_cart_unique_together'),
    ]

    # State-only: `Card` already exists as the `binders_card` table (created
    # by binders' own initial migration). This just moves it into this app's
    # migration state — no schema change, no data migration.
    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.CreateModel(
                    name='Card',
                    fields=[
                        ('id', models.CharField(max_length=255, primary_key=True, serialize=False)),
                        ('name', models.CharField(db_index=True, max_length=255)),
                        ('set_name', models.CharField(max_length=255)),
                        ('set_code', models.CharField(blank=True, default='', max_length=10)),
                        ('color_identity', models.CharField(max_length=255)),
                        ('type_line', models.CharField(blank=True, default='', max_length=255)),
                        ('uri', models.CharField(max_length=512)),
                        ('scryfall_uri', models.CharField(max_length=512)),
                        ('image_uri', models.URLField(blank=True, default='', max_length=512)),
                        ('price_usd', models.DecimalField(decimal_places=2, max_digits=12, null=True)),
                        ('price_usd_foil', models.DecimalField(decimal_places=2, max_digits=12, null=True)),
                        ('price_usd_etched', models.DecimalField(decimal_places=2, max_digits=12, null=True)),
                        ('phash', models.CharField(blank=True, default='', max_length=16)),
                        ('binders', models.ManyToManyField(blank=True, through='binders.BinderCard', to='binders.binder')),
                    ],
                    options={
                        'db_table': 'binders_card',
                    },
                ),
            ],
            database_operations=[],
        ),
    ]
